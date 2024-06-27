import os
import logging
from datetime import datetime
from logger import logger
from slack_bolt import App
from slack_sdk.web import WebClient
from dotenv import load_dotenv
import requests
import pdf
from slack_bolt.adapter.socket_mode import SocketModeHandler

# 環境変数をロード
load_dotenv()

# 動作確認用にデバッグレベルのロギングを有効にします
# 本番運用では削除しても構いません
logging.basicConfig(level=logging.DEBUG)

# ロガーのセットアップ
LOG = logger(__name__)

# Slackクライアントのセットアップ
client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
#app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
app = App(
    # リクエストの検証に必要な値
    # Settings > Basic Information > App Credentials > Signing Secret で取得可能な値
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
    # 上でインストールしたときに発行されたアクセストークン
    # Settings > Install App で取得可能な値
    token=os.environ["SLACK_BOT_TOKEN"],
    # AWS Lamdba では、必ずこの設定を true にしておく必要があります
    process_before_response=True,
)
channel = os.environ.get("CHANNEL")

# タイムスタンプをフォーマットする関数
def format_timestamp(ts):
    dt = datetime.fromtimestamp(float(ts))
    return dt.strftime('%Y/%m/%d %H:%M:%S')

# メッセージからファイルを取得する関数
def get_files_from_messages(messages):
    files = []
    for message in messages:
        files.extend(message.get("files", []))
    return files

# ショートカットがトリガーされたときの処理
@app.shortcut("message_save")
def message_shortcut(ack, shortcut, client, body):
    try:
        LOG.debug("shortcut")
        ack()

        # ユーザー情報を取得
        user_id = shortcut["user"]["id"]
        user_info = client.users_info(user=user_id)
        user_name = user_info["user"]["real_name"]

        # チャンネルIDとメッセージタイムスタンプを取得
        channel_id = shortcut["channel"]["id"]
        message_ts = shortcut["message"]["ts"]
        thread_ts = shortcut["message"].get("thread_ts")

        # チャンネルが指定されたチャンネルであれば処理を終了
        if channel_id == channel:
            print('終了')
            return

        # メッセージの詳細を取得
        message_response = client.conversations_history(
            channel=channel_id,
            latest=message_ts,
            inclusive=True,
            limit=1  # 取得するメッセージを1つに制限
        )
        
        message = message_response["messages"][0]
        message_user_id = message["user"]
        message_time = message["ts"]
        date = format_timestamp(message_time)
        message_link = f"https://slack.com/archives/{channel_id}/p{message_time.replace('.', '')}"
        message_user_info = client.users_info(user=message_user_id)
        message_user_name = message_user_info["user"]["real_name"]
        message_files = get_files_from_messages([message])

        # コンテンツの生成
        content = f"このメッセージ保存を実行したユーザー: {user_name} (<@{user_id}>)"
        content += (f"\n\n投稿者: {message_user_name} (<@{message_user_id}>)\n"
                   f"日時: {date}\n"
                   f"リンク: {message_link}\n"
                   f"メッセージ:\n{message['text']}\n\n")

        # スレッドが存在する場合、スレッドの詳細を追加
        if thread_ts:
            thread_response = client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                inclusive=True
            )
            thread_files = get_files_from_messages(thread_response["messages"])
            thread_messages = thread_response["messages"]
            thread_text = "\n".join([f"投稿者:<@{thread['user']}>\n日時: {format_timestamp(thread['ts'])}\nメッセージ {i}: {thread['text']}" for i, thread in enumerate(thread_messages[1:], 1)])
            content += f"スレッド:\n{thread_text}"

        # PDFを生成
        pdf_file_path = "message.pdf"
        pdf.create_pdf(content, pdf_file_path)
        LOG.debug("File Create")

        # 新しいメッセージを別のチャンネルに投稿し、そのスレッドにPDFを添付
        new_message = client.chat_postMessage(
            channel=channel,
            text=content
        )
        new_thread_ts = new_message["ts"]
        client.files_upload_v2(
            channels=channel,
            file=pdf_file_path,
            title="Message and Thread PDF",
            initial_comment="Here is the PDF containing the message and its thread.",
            thread_ts=new_thread_ts
        )

        # 元のメッセージとスレッド内のファイルを新しいメッセージのスレッドに添付
        all_files = message_files + (thread_files if thread_ts else [])
        for file in all_files:
            file_id = file["id"]
            file_info = client.files_info(file=file_id)
            file_name = file_info["file"]["name"]
            file_url = file_info["file"]["url_private"]
            response = requests.get(file_url, headers={"Authorization": f"Bearer {os.environ.get('SLACK_BOT_TOKEN')}"})
            file_content = response.content
            response = client.files_upload_v2(
                channels=channel,
                file=file_content,
                filename=file_name,
                thread_ts=new_thread_ts
            )
            LOG.debug(f"File upload response: {response}")

        # 元のスレッドにリアクションを追加
        client.reactions_add(
            channel=channel_id,
            name="white_check_mark",
            timestamp=message_ts
        )
        #元のスレッドからリアクションを削除
        # client.reactions_remove(
        #     channel=channel_id,
        #     name="white_check_mark",
        #     timestamp=message_ts
        # )
    except Exception as e:
        LOG.error(f"Error publishing home tab: {e}")
        # Rate Limitの場合、処理失敗のエラーハンドリング

# メイン処理
if __name__ == "__main__":
    app.start(3000)
    #handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    LOG.debug("server start")
    #handler.start()
