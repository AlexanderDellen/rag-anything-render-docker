import os
import asyncio
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from raganything import RAGAnything, RAGAnythingConfig
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")  # optional (z.B. OpenRouter)
WORKDIR = os.getenv("WORKDIR", "/data/rag_storage")

# Parser-Wahl:
# - "docling": leicht & stabil; mit Docker + LibreOffice kannst du Office-Dateien verarbeiten
# - "mineru": mächtiger (OCR/VLM), kostet mehr Ressourcen – später umstellbar
config = RAGAnythingConfig(
    working_dir=WORKDIR,
    parser="docling",
    parse_method="auto",
    enable_image_processing=True,
    enable_table_processing=True,
    enable_equation_processing=True,
)

def llm_model_func(prompt, system_prompt=None, history_messages=None, **kwargs):
    if history_messages is None:
        history_messages = []
    return openai_complete_if_cache(
        "gpt-4o-mini",
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        **kwargs,
    )

embedding_func = EmbeddingFunc(
    embedding_dim=3072,
    max_token_size=8192,
    func=lambda texts: openai_embed(
        texts, model="text-embedding-3-large",
        api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL
    ),
)

app = FastAPI()
rag = RAGAnything(
    config=config,
    llm_model_func=llm_model_func,
    embedding_func=embedding_func,
)

@app.get("/healthz")
async def healthz():
    return {"ok": True}

@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    os.makedirs("/data/uploads", exist_ok=True)
    dst = f"/data/uploads/{file.filename}"
    with open(dst, "wb") as f:
        f.write(await file.read())
    await rag.process_document_complete(file_path=dst, output_dir="/data/output")
    return {"status": "ingested", "file": file.filename}

@app.post("/query")
async def query(q: str = Form(...), mode: str = Form("hybrid")):
    result = await rag.aquery(q, mode=mode)  # modes: hybrid | local | global | naive
    return JSONResponse({"answer": result})
