# utils.py

import qrcode
from io import BytesIO
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap

def criar_qr_code(url: str, tamanho: int = 150) -> QPixmap:
    """Gera uma imagem QPixmap de um QR Code a partir de uma URL."""
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img_pil = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img_pil.save(buffer, format='PNG')
        buffer.seek(0)
        
        qimagem = QImage.fromData(buffer.getvalue())
        return QPixmap.fromImage(qimagem).scaled(
            tamanho, tamanho, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
    except Exception as e:
        print(f"Erro ao criar QR code: {e}")
        return QPixmap()