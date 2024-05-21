import logging
import os, sys
from dotenv import load_dotenv;
load_dotenv()

def logger(name:str):
    # ログレベル定義
    level = os.environ["LOGGING_LEVEL"] if "LOGGING_LEVEL" in os.environ else 'INFO'
    # フォーマット定義
    formatter = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    # 出力先ファイル定義
    file_path = './output.log'

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(formatter))

    # 各種定義 を logging.basicConfig に渡す
    logging.basicConfig(level=level, 
                        format=formatter, 
                        filename=file_path)

    LOG = logging.getLogger(name)
    LOG.addHandler(handler)
    return LOG