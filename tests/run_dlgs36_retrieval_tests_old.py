from pathlib import Path
import json
import chromadb
from chromadb.utils import embedding_functions

PERSIST_DIR = "data/chroma"
OUTPUT_JSON = Path("data/processed/retrieval_tests/dlgs36_retrieval_results.json")

COLLECTIONS = {
    "main": "normattiva_dlgs36_2023_articles",
    "i1": "normattiva_dlgs36_2023_all_i1",
    "i2": "normattiva_dlgs36_2023_all_i2",
    "ii1": "normattiva_dlgs36_2023_all_ii1",
    "ii4": "normattiva_dlgs36_2023_all_ii4",
    "ii14": "normattiva_dlgs36_2023_all_ii14",
}

TEST_QUERIES = [
    "affidamento diretto sotto soglia",
    "principio di rotazione",
    "responsabile unico del progetto",
    "procedure negoziate senza bando",
    "offerta economicamente più vantaggiosa",
    "stazione appaltante definizione",
    "operatore economico definizione",
    "attività del rup",
    "indagini di mercato",
    "qualificazione stazioni appaltanti",
    "direzione dei lavori",
    "certificato di regolare esecuzione",
]

def main():
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    loaded = {}
    for key, name in COLLECTIONS.items():
        loaded[key] = client.get_collection(name=name, embedding_function=embedding_fn)

    results_dump = {
        "persist_dir": PERSIST_DIR,
        "collections": COLLECTIONS,
        "queries": []
    }

    print("=== RETRIEVAL TEST D.LGS. 36/2023 ===")
    print("Collections attive:")
    for key, name in COLLECTIONS.items():
        print(f"- {key}: {name}")

    for query in TEST_QUERIES:
        print("\n" + "=" * 100)
        print(f"QUERY: {query}")
        print("=" * 100)

        query_result = {
            "query": query,
            "collections": {}
        }

        for key, coll in loaded.items():
            res = coll.query(query_texts=[query], n_results=3)

            docs = res.get("documents", [[]])[0]
            metas = res.get("metadatas", [[]])[0]
            ids = res.get("ids", [[]])[0]

            query_result["collections"][key] = []

            print(f"\n[{key}]")
            if not docs:
                print("  nessun risultato")
                continue

            for i, (doc, meta, rid) in enumerate(zip(docs, metas, ids), start=1):
                articolo = meta.get("articolo", "")
                allegato = meta.get("allegato", "")
                src = meta.get("source_id", "")
                preview = doc[:250].replace("\n", " ")

                print(f"  {i}. id={rid}")
                print(f"     articolo={articolo} allegato={allegato} source={src}")
                print(f"     {preview}")

                query_result["collections"][key].append({
                    "rank": i,
                    "id": rid,
                    "articolo": articolo,
                    "allegato": allegato,
                    "source_id": src,
                    "preview": preview,
                })

        results_dump["queries"].append(query_result)

    OUTPUT_JSON.write_text(
        json.dumps(results_dump, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("\n" + "=" * 100)
    print(f"[OK] file risultati scritto in: {OUTPUT_JSON}")
    print("=" * 100)

if __name__ == "__main__":
    main()
