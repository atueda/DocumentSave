import os
from datetime import datetime
from logger import logger
from slack_bolt import App
from slack_sdk.web import WebClient
from dotenv import load_dotenv
import requests
#from create_pdf import
import pdf
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()

LOG = logger(__name__)
client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
# Initialize a Bolt for Python app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    #signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
#user_client = WebClient(token=os.environ.get("SLACK_USER_TOKEN"))

def format_timestamp(ts):
    dt = datetime.fromtimestamp(float(ts))
    return dt.strftime('%Y/%m/%d %H:%M:%S')

# メッセージショートカットのアクションを処理する
@app.shortcut("message_save")
def message_shortcut(ack, shortcut, client, body):
    try:
        LOG.debug(f"shortcut")
        # ショートカットリクエストを確認
        ack()

        # メッセージとスレッドの情報を取得
        channel_id = shortcut["channel"]["id"]
        message_ts = shortcut["message"]["ts"]
        thread_ts = shortcut["message"]["thread_ts"]

        # メッセージとそのスレッドを取得
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

        # メッセージのユーザー名、タイムスタンプ、リンクを取得
        message_user_id = message_response["messages"][0]["user"]
        message_time = message_response["messages"][0]["ts"]
        dt = datetime.fromtimestamp(float(message_time))
        date = dt.strftime('%Y/%m/%d %H:%M:%S')
        message_link = f"https://slack.com/archives/{channel_id}/p{message_time.replace('.', '')}"
        
        # ユーザー名を取得
        user_info = client.users_info(user=message_user_id)
        message_user_name = user_info["user"]["real_name"]
        

        thread_messages = thread_response["messages"]
        # スレッドのユーザー名、タイムスタンプ、リンクを取得
        thread_messages = thread_response["messages"]
        thread_user = thread_messages[0]["user"]
        thread_time = thread_messages[0]["ts"]
        thread_link = f"https://slack.com/archives/{channel_id}/p{thread_time.replace('.', '')}"
        # スレッドのテキストを連結
        thread_text = "\n".join([f"投稿者:{thread['user']}\n日時: {format_timestamp(thread['ts'])}\nメッセージ {i}: {thread['text']}" for i, thread in enumerate(thread_messages[1:], 1)])

        # メッセージ内容を作成
        content = (f"投稿者: {message_user_name} (<@{message_user_id}>)\n"
                   f"日時: {date}\n"
                   f"リンク: {message_link}\n"
                   f"メッセージ:\n{message_response['messages'][0]['text']}\n\n"
                   f"スレッド:\n{thread_text}")

        # 取得したメッセージとスレッドを別のワークスペースに投稿
        channel_id = "C073SBTH8Q4"
        client.chat_postMessage(
            channel=channel_id,
            text=content
        )
        # PDFを生成
        pdf_file_path = "message.pdf"
        pdf.create_pdf(content, pdf_file_path)
        #pdf12.create_pdf(pdf_file_path)
        LOG.debug(f"File Create")
        # PDFをSlackにアップロード
        response = client.files_upload_v2(
            filename=pdf_file_path,
            channels="C073SBTH8Q4",
            file=pdf_file_path,
            title="Message and Thread PDF",
            initial_comment="Here is the PDF containing the message and its thread."
        )

        LOG.debug(f"File upload response: {response}")
        
# def message_shortcut(ack, shortcut, client, body):
#   try:
#     LOG.debug(f"shortcut")
#     # ショートカットリクエストを確認
#     ack()

#     # メッセージとスレッドの情報を取得
#     channel_id = shortcut["channel"]["id"]
#     message_ts = shortcut["message"]["ts"]
#     thread_ts = shortcut["message"]["thread_ts"]

#     # メッセージとそのスレッドを取得
#     message_response = client.conversations_history(
#         channel=channel_id,
#         latest=message_ts,
#         inclusive=True
#     )
#     thread_response = client.conversations_replies(
#         channel=channel_id,
#         ts=thread_ts,
#         inclusive=True
#     )

#     # メッセージのユーザー名、タイムスタンプ、リンクを取得
#     message_user = message_response["messages"][0]["user"]
#     message_time = message_response["messages"][0]["ts"]
#     message_link = f"https://slack.com/archives/{channel_id}/p{message_time.replace('.', '')}"

#     # スレッドのユーザー名、タイムスタンプ、リンクを取得
#     thread_messages = thread_response["messages"]
#     thread_user = thread_messages[0]["user"]
#     thread_time = thread_messages[0]["ts"]
#     thread_link = f"https://slack.com/archives/{channel_id}/p{thread_time.replace('.', '')}"

#     # スレッドのテキストを連結
#     thread_text = "\n".join([f"スレッドメッセージ {i+1}: {thread['text']}" for i, thread in enumerate(thread_messages)])

#     # 取得したメッセージとスレッドを別のワークスペースに投稿
#     channel_id = "C073SBTH8Q4"
#     client.chat_postMessage(
#         channel=channel_id,
#         text=f"ユーザー名: {message_user}\nタイムスタンプ: {message_time}\nリンク: {message_link}\nメッセージ:\n{message_response['messages'][0]['text']}\n\nスレッド:\n{thread_text}"
#         # text=f"メッセージ: {message_response['messages'][0]['text']}\nユーザー名: {message_user}\nタイムスタンプ: {message_time}\nリンク: {message_link}\n\nスレッド: {thread_text}\n\nスレッドユーザー名: {thread_user}\nスレッドタイムスタンプ: {thread_time}\nスレッドリンク: {thread_link}"
#     )
    except Exception as e:
        LOG.error(f"Error publishing home tab: {e}")
    
@app.event("app_home_opened")
def update_home_tab(client: WebClient, event, logger):
    LOG.debug("app_home_opened")
    try:
        client.views_publish(
            user_id=event["user"],
            view={
                "type": "home",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Welcome home, <@" + event["user"] + "> :house:*"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                          "type": "mrkdwn",
                          "text":"Learn how home tabs can be more useful and interactive <https://api.slack.com/surfaces/tabs/using|*in the documentation*>."
                        }
                    },
                    {
                        "type": "actions",
                        "block_id": "file_id_search_actions",
                        "elements": [
                            {
                                "type": "button",
                                "action_id": "file_id_search_submit",
                                "text": {
                                    "type": "plain_text",
                                    "text": "File ID Search"
                                }
                            }
                        ]
                    },
                    {
                        "label": {
                            "type": "plain_text",
                            "text": "File ID",
                            "emoji": True
                        },
                        "type": "input",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "file_id_input_action"
                        }
                    },
                    {
                        "type": "actions",
                        "block_id": "file_id_actions",
                        "elements": [
                            {
                                "type": "button",
                                "action_id": "file_id_submit",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Submit"
                                }
                            }
                        ]
                    }
                ]
            }
        )
    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")

# Start server
# def start_server():
if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    LOG.debug("server start")
    handler.start()
# if __name__ == "__main__":
#     handler = SocketModeHandler(
#         app=app,
#         app_token=os.environ["SLACK_APP_TOKEN"],
#         trace_enabled=True,
#     )
#     handler.start()