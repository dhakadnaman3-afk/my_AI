from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import urllib.parse
import io
import csv
import json

from pypdf import PdfReader
from docx import Document
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

from app.chat import get_response, get_response_stream, regenerate_response_stream
from app.database import ( 
    get_history, get_conversations, delete_conversation, rename_conversation,
    search_messages
)

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")


class ChatRequest(BaseModel):
    message: str
    session_id: str
    file_context: Optional[str] = None
    model: Optional[str] = None


class RenameRequest(BaseModel):
    title: str


class RegenerateRequest(BaseModel):
    session_id: str
    model: Optional[str] = None


@app.get("/")
def home():
    return FileResponse("app/static/index.html")


@app.post("/chat")
def chat(req: ChatRequest):
    reply = get_response(req.session_id, req.message, req.file_context, req.model)
    return {"reply": reply}


@app.post("/chat-stream")
def chat_stream(req: ChatRequest):
    return StreamingResponse(
        get_response_stream(req.session_id, req.message, req.file_context, req.model),
        media_type="text/plain"
    )


@app.post("/regenerate")
def regenerate(req: RegenerateRequest):
    return StreamingResponse(
        regenerate_response_stream(req.session_id, req.model),
        media_type="text/plain"
    )


@app.get("/history/{session_id}")
def history(session_id: str):
    rows = get_history(session_id)
    messages = [{"role": role, "content": content} for role, content in rows]
    return {"messages": messages}


@app.get("/conversations")
def conversations():
    return {"conversations": get_conversations()}


@app.get("/search")
def search(q: str):
    return {"results": search_messages(q)}


@app.delete("/conversations/{session_id}")
def remove_conversation(session_id: str):
    delete_conversation(session_id)
    return {"status": "deleted"}


@app.put("/conversations/{session_id}")
def rename(session_id: str, req: RenameRequest):
    rename_conversation(session_id, req.title)
    return {"status": "renamed"}


@app.post("/generate-image")
def generate_image(req: ChatRequest):
    prompt = urllib.parse.quote(req.message)
    image_url = f"https://image.pollinations.ai/prompt/{prompt}"
    return {"image_url": image_url}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    filename = file.filename.lower()

    try:
        text = ""

        if filename.endswith(".pdf"):
            reader = PdfReader(io.BytesIO(content))
            for page in reader.pages:
                text += page.extract_text() or ""

        elif filename.endswith(".txt"):
            text = content.decode("utf-8", errors="ignore")

        elif filename.endswith(".docx"):
            doc = Document(io.BytesIO(content))
            text = "\n".join([para.text for para in doc.paragraphs])

        elif filename.endswith(".csv"):
            decoded = content.decode("utf-8", errors="ignore")
            reader = csv.reader(io.StringIO(decoded))
            rows = list(reader)
            text = "\n".join([", ".join(row) for row in rows])

        elif filename.endswith(".json"):
            decoded = content.decode("utf-8", errors="ignore")
            parsed = json.loads(decoded)
            text = json.dumps(parsed, indent=2)

        elif filename.endswith((".jpg", ".jpeg", ".png")):
            image = Image.open(io.BytesIO(content))
            text = pytesseract.image_to_string(image)

        else:
            return {"error": "Supported formats: .pdf, .txt, .docx, .csv, .json, .jpg, .png"}

        if not text.strip():
            return {"error": "Could not extract any text from this file."}

        return {"text": text, "filename": file.filename}

    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}