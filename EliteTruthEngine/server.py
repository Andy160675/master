from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from txtai.embeddings import Embeddings
from llama_cpp import Llama
import os

INDEX_PATH = os.getenv("ELITE_INDEX", r"C:\EliteTruthEngine\elite-truth-index")
MODEL_PATH = os.getenv("ELITE_MODEL", r"C:\EliteTruthEngine\models\llama-3.1-8b-q8.gguf")

app = FastAPI()

# Distributed deployment support (Electron/React UI may run on a different host).
# Configure via TRUTH_ENGINE_CORS_ORIGINS:
#   - "*" (default) allows all origins
#   - or a comma-separated list of allowed origins, e.g. "http://localhost:5173,http://192.168.4.114:5173"
cors_origins_raw = os.getenv("TRUTH_ENGINE_CORS_ORIGINS", "*").strip()
if cors_origins_raw == "*":
    allow_origins = ["*"]
else:
    allow_origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["*"] ,
    allow_headers=["*"] ,
)
embeddings = Embeddings()
embeddings.load(INDEX_PATH)

llm = Llama(model_path=MODEL_PATH, n_ctx=4096, n_threads=8)

SYSTEM_PROMPT = (
"You are the Sovereign Truth Engine.\n"
"Answer ONLY using the provided context. If insufficient, say so explicitly.\n"
"Always cite [file ids] inside the answer when referring to evidence.\n"
)

class TruthQuery(BaseModel):
    question: str
    k: int = 5

@app.post("/truth/query")
def truth_query(payload: TruthQuery):
    results = embeddings.search(payload.question, payload.k)
    if not results:
        return {"answer": "No relevant documents in index.", "cites": []}

    blocks = []
    cites = []
    for r in results:
        doc_id = r.get("id")
        text = r.get("text", "")
        score = float(r.get("score", 0.0))
        blocks.append(f"[{doc_id}]\n{text}\n")
        cites.append({"id": doc_id, "score": score})

    context = "\n\n".join(blocks)
    prompt = f"{SYSTEM_PROMPT}\nContext:\n{context}\nQuestion: {payload.question}\nAnswer (with [file ids] in-line):\n"

    out = llm(prompt, max_tokens=512, stop=["Question:", "Context:"])
    answer = out["choices"][0]["text"].strip()
    return {"answer": answer, "cites": cites}
