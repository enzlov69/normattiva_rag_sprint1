import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb

# -----------------------------
# CONFIG
# -----------------------------

INPUT_FILE = Path("data/processed/tuel/tuel_rag_ready.json")
CHROMA_DIR = "data/chroma"
COLLECTION_NAME = "norme"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# -----------------------------
# LOAD MODEL
# -----------------------------

print("Carico modello embedding...")
model = SentenceTransformer(MODEL_NAME)

# -----------------------------
# LOAD DATA
# -----------------------------

print("Carico TUEL...")

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    payload = json.load(f)

articles = payload.get("articles", [])

print("Articoli caricati:", len(articles))

# -----------------------------
# INIT CHROMA
# -----------------------------

client = chromadb.PersistentClient(path=CHROMA_DIR)

collection = client.get_or_create_collection(name=COLLECTION_NAME)

# -----------------------------
# BUILD CHUNKS
# -----------------------------

documents = []
metadatas = []
ids = []

print("Costruzione chunk...")

for art in articles:
    articolo = art.get("articolo", "")
    rubrica = art.get("rubrica", "")
    testo = art.get("testo", "")

    if not testo:
        continue

    doc_text = f"Articolo {articolo} - {rubrica}\n\n{testo}".strip()
    doc_id = f"TUEL_art_{articolo}"

    documents.append(doc_text)
    metadatas.append({
        "norma": "D.Lgs. 267/2000",
        "sigla_norma": "TUEL",
        "articolo": articolo,
        "rubrica": rubrica,
    })
    ids.append(doc_id)

print("Chunk creati:", len(documents))

# -----------------------------
# EMBEDDINGS
# -----------------------------

print("Genero embeddings...")
embeddings = model.encode(documents).tolist()

# -----------------------------
# INSERT IN CHROMA
# -----------------------------

print("Inserisco in ChromaDB...")
collection.add(
    documents=documents,
    embeddings=embeddings,
    metadatas=metadatas,
    ids=ids,
)

print("Ingestione completata.")
print("Vector store salvato in:", CHROMA_DIR)