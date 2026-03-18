from fastapi import APIRouter, File, UploadFile

router = APIRouter(prefix="/api/ocr", tags=["ocr"])
from app.services.ocr_service import parse_image_bytes


@router.post("/parse")
async def parse_ocr(file: UploadFile = File(...)) -> dict:
    filename = file.filename or "upload"
    image_bytes = await file.read()
    text, engine = parse_image_bytes(image_bytes, filename)
    return {"text": text, "filename": filename, "engine": engine}
