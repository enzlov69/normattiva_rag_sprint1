from __future__ import annotations

from _common import (
    COLLECTION_NAME,
    DEFAULT_CHROMA_PATH,
    DEFAULT_EMBED_MODEL,
    SMOKE_QUERIES,
    count_collection,
    encode_query,
    get_client,
    get_collection,
    load_model,
    preview_text,
    print_header,
    safe_peek_ids,
)


def main() -> None:
    print_header("SMOKE TEST L241")
    print(f"COLLECTION   : {COLLECTION_NAME}")
    print(f"CHROMA_PATH  : {DEFAULT_CHROMA_PATH}")
    print(f"EMBED_MODEL  : {DEFAULT_EMBED_MODEL}")
    print()

    client = get_client(DEFAULT_CHROMA_PATH)
    collection = get_collection(client, COLLECTION_NAME)

    count = count_collection(collection)
    peek_ids = safe_peek_ids(collection, limit=3)

    print(f"COUNT       : {count}")
    print(f"PEEK_IDS    : {peek_ids}")
    print()

    if count <= 0:
        raise SystemExit("[ERRORE] Collection vuota o non leggibile.")

    model = load_model(DEFAULT_EMBED_MODEL)

    for query in SMOKE_QUERIES:
        print(f"[QUERY] {query}")
        query_embedding = encode_query(model, query)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3,
            include=["documents", "metadatas", "distances"],
        )

        ids = (results.get("ids") or [[]])[0]
        docs = (results.get("documents") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]

        if not ids:
            raise SystemExit(f"[ERRORE] Nessun risultato per query: {query}")

        for idx, rid in enumerate(ids, start=1):
            doc = docs[idx - 1] if idx - 1 < len(docs) else ""
            dist = distances[idx - 1] if idx - 1 < len(distances) else None
            dist_txt = f"{dist:.6f}" if isinstance(dist, (int, float)) else "n/a"
            print(
                f"  [{idx}] id={rid} | distance={dist_txt} | text={preview_text(doc, 180)}"
            )
        print()

    print("[ESITO] SMOKE OK")


if __name__ == "__main__":
    main()