
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl

from pathlib import Path
from datetime import datetime
from uuid import uuid4

import qrcode
import io
import base64

app = FastAPI(
    title="Professional QR Code Generator",
    description="Generate, save, download and share QR codes."
)

BASE_DIR = Path(__file__).resolve().parent

TEMPLATE_DIR = BASE_DIR / "templates"
QR_DIR = BASE_DIR / "generated_qrs"

QR_DIR.mkdir(parents=True, exist_ok=True)

app.mount(
    "/qr-files",
    StaticFiles(directory=str(QR_DIR)),
    name="qr-files"
)

@app.get("/", response_class=HTMLResponse)
def home():

    html_file = TEMPLATE_DIR / "home.html"

    if not html_file.exists():
        raise HTTPException(
            status_code=404,
            detail="HTML file not found"
        )

    return html_file.read_text(encoding="utf-8")

class LinkData(BaseModel):
    link: str

@app.post("/routes")
def convert(data: LinkData):

    link = str(data.link).strip()

    try:
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )

        qr.add_data(link)
        qr.make(fit=True)

        img = qr.make_image(
            fill_color="black",
            back_color="white"
        ).convert("RGB")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        unique_id = uuid4().hex[:8]

        filename = f"QR_{timestamp}_{unique_id}.png"

        file_path = QR_DIR / filename

        img.save(file_path, format="PNG")
        img_buffer = io.BytesIO()

        img.save(img_buffer, format="PNG")

        img_base64 = base64.b64encode(
            img_buffer.getvalue()
        ).decode("utf-8")

        return {
            "success": True,
            "message": "QR Code generated successfully!",
            "link": link,
            "filename": filename,
            "qr_code": img_base64,
            "image_url": f"/qr-files/{filename}"
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"QR generation failed: {str(e)}"
        )

@app.get("/api/qrs")
def saved_qrs():

    files = sorted(
        QR_DIR.glob("*.png"),
        key=lambda file: file.stat().st_mtime,
        reverse=True
    )

    return {
        "total": len(files),
        "qrs": [
            {
                "filename": file.name,
                "image_url": f"/qr-files/{file.name}"
            }
            for file in files
        ]
    }
