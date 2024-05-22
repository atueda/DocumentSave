import os
from datetime import datetime
from logger import logger
from slack_bolt import App
from slack_sdk.web import WebClient
from dotenv import load_dotenv
import requests
import pdf
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()

LOG = logger(__name__)
client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

def format_timestamp(ts):
    dt = datetime.fromtimestamp(float(ts))
    return dt.strftime('%Y/%m/%d %H:%M:%S')

def get_files_from_messages(messages):
    files = []
    for message in messages:
        files.extend(message.get("files", []))
    return files

@app.shortcut("message_save")
def message_shortcut(ack, shortcut, client, body):
    try:
        LOG.debug(f"shortcut")
        ack()

        channel_id = shortcut["channel"]["id"]
        message_ts = shortcut["message"]["ts"]
        thread_ts = shortcut["message"]["thread_ts"]

        message_response = client.conversations_history(
            channel=channel_id,
            latest=message_ts,
            inclusive=True
        )
        thread_response = client.conversations_replies(
            channel=channel_id,
            ts=thread_ts,
            inclusive=True
        )

        message_user_id = message_response["messages"][0]["user"]
        message_time = message_response["messages"][0]["ts"]
        date = format_timestamp(message_time)
        message_link = f"https://slack.com/archives/{channel_id}/p{message_time.replace('.', '')}"
        
        user_info = client.users_info(user=message_user_id)
        message_user_name = user_info["user"]["real_name"]

        message_files = get_files_from_messages(message_response["messages"])
        thread_files = get_files_from_messages(thread_response["messages"])
        
        thread_messages = thread_response["messages"]
        thread_text = "\n".join([f"投稿者:<@{thread['user']}>\n日時: {format_timestamp(thread['ts'])}\nメッセージ {i}: {thread['text']}" for i, thread in enumerate(thread_messages[1:], 1)])

        content = (f"投稿者: {message_user_name} (<@{message_user_id}>)\n"
                   f"日時: {date}\n"
                   f"リンク: {message_link}\n"
                   f"メッセージ:\n{message_response['messages'][0]['text']}\n\n"
                   f"スレッド:\n{thread_text}")

        # PDFを生成
        pdf_file_path = "message.pdf"
        pdf.create_pdf(content, pdf_file_path)
        LOG.debug(f"File Create")

        # 新しいメッセージを別のチャンネルに投稿し、そのスレッドにPDFを添付
        new_message = client.chat_postMessage(
            channel="C073SBTH8Q4",
            text=content
        )

        new_thread_ts = new_message["ts"]

        client.files_upload_v2(
            channels="C073SBTH8Q4",
            file=pdf_file_path,
            title="Message and Thread PDF",
            initial_comment="Here is the PDF containing the message and its thread.",
            thread_ts=new_thread_ts
        )

        # 元のメッセージとスレッド内のファイルを新しいメッセージのスレッドに添付
        all_files = message_files + thread_files
        for file in all_files:
            file_id = file["id"]
            file_info = client.files_info(file=file_id)
            file_name = file_info["file"]["name"]
            file_url = file_info["file"]["url_private"]

            response = requests.get(file_url, headers={"Authorization": f"Bearer {os.environ.get('SLACK_BOT_TOKEN')}"})
            file_content = response.content

            response = client.files_upload_v2(
                channels="C073SBTH8Q4",
                file=file_content,
                filename=file_name,
                thread_ts=new_thread_ts
            )
            LOG.debug(f"File upload response: {response}")
        
    except Exception as e:
        LOG.error(f"Error publishing home tab: {e}")

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    LOG.debug("server start")
    handler.start()