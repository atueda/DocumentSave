from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
import io
import logging

LOG = logging.getLogger(__name__)

def create_pdf(content, file_path):
  try:
        # 日本語フォントを読み込む
        #pdfmetrics.registerFont(TTFont('IPAGothic', 'ipag.ttf'))
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5')) #フォント
        
        c = canvas.Canvas(file_path, pagesize=A4)

        # 日本語フォントを設定
        c.setFont("HeiseiKakuGo-W5", 12)

        # テキストの描画
        text_lines = content.split('\n')
        y_position = 750  # 垂直位置
        for line in text_lines:
            c.drawString(50, y_position, line)
            y_position -= 20  # 改行のために20ポイント下に移動

        c.save()
  except Exception as e:
      LOG.error(f"Error creating PDF: {e}")