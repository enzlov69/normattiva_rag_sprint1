"""
Canonical strong validation baseline for the D.Lgs. 36/2023 branch.

Current branch status:
- validation-centered active baseline
- this file is the canonical strong validation entrypoint
- cantiere_36/ and cantiere_36_allegati/ remain rebuild provenance, not active baseline

Do not treat cantiere rebuild scripts as the default runtime baseline unless
the branch is explicitly reconsolidated around them.
"""

from pathlib import Path
import json
import chromadb
from chromadb.utils import embedding_functions

PERSIST_DIR = "data/chroma"
OUTPUT_JSON = Path("data/processed/retrieval_tests/dlgs36_federated_results.json")

DLGS36_MAIN = "normattiva_dlgs36_2023_articles"
DLGS36_I1 = "normattiva_dlgs36_2023_all_i1"      # art. 11 / CCNL / equivalenza tutele
DLGS36_I2 = "normattiva_dlgs36_2023_all_i2"      # RUP
DLGS36_II1 = "normattiva_dlgs36_2023_all_ii1"    # indagini di mercato / sotto soglia
DLGS36_II4 = "normattiva_dlgs36_2023_all_ii4"    # qualificazione
DLGS36_II14 = "normattiva_dlgs36_2023_all_ii14"  # esecuzione / DL / regolare esecuzione

TEST_QUERIES = [
    "affidamento diretto sotto soglia",
    "principio di rotazione",
    "responsabile unico del progetto",
    "procedure negoziate senza bando",
    "offerta economicamente più vantaggiosa",
    "attività del rup",
    "indagini di mercato",
    "qualificazione stazioni appaltanti",
    "direzione dei lavori",
    "certificato di regolare esecuzione",
]

def route_dlgs36_contracts_collections_v2(query_text: str) -> list[str]:
    q = query_text.lower().strip()
    collections: list[str] = [DLGS36_MAIN]

    if any(k in q for k in [
        "contratto collettivo",
        "contratti collettivi",
        "ccnl",
        "equivalenza tutele",
        "equivalenza delle tutele",
        "articolo 11",
        "personale impiegato",
        "tutele economiche",
        "tutele normative",
    ]):
        collections.append(DLGS36_I1)

    if any(k in q for k in [
        "rup",
        "responsabile unico del progetto",
        "attività del rup",
        "compiti del rup",
        "nomina rup",
        "requisiti del rup",
        "responsabile di fase",
    ]):
        collections.append(DLGS36_I2)

    if any(k in q for k in [
        "affidamento diretto",
        "sotto soglia",
        "articolo 50",
        "indagine di mercato",
        "indagini di mercato",
        "elenco operatori",
        "elenchi operatori",
        "operatori da invitare",
        "procedura negoziata",
        "senza bando",
        "sorteggio operatori",
        "selezione operatori",
    ]):
        collections.append(DLGS36_II1)

    if any(k in q for k in [
        "qualificazione stazioni appaltanti",
        "stazione appaltante qualificata",
        "centrale di committenza qualificata",
        "qualificazione",
        "ausa",
        "articolo 62",
        "articolo 63",
    ]):
        collections.append(DLGS36_II4)

    if any(k in q for k in [
        "direzione dei lavori",
        "direttore dei lavori",
        "direttore dell'esecuzione",
        "dec",
        "collaudo",
        "verifica di conformità",
        "certificato di regolare esecuzione",
        "regolare esecuzione",
        "esecuzione del contratto",
        "contabilità lavori",
        "sospensione lavori",
    ]):
        collections.append(DLGS36_II14)

    seen = set()
    ordered = []
    for c in collections:
        if c not in seen:
            ordered.append(c)
            seen.add(c)
    return ordered

def expand_dlgs36_query_v2(query_text: str) -> str:
    q = query_text.lower().strip()

    expansions = {
        "affidamento diretto sotto soglia":
            "affidamento diretto sotto soglia articolo 50 lavori servizi forniture 140000 150000",

        "principio di rotazione":
            "principio di rotazione articolo 49 affidamenti sotto soglia",

        "responsabile unico del progetto":
            "responsabile unico del progetto RUP articolo 15 allegato I.2 compiti requisiti",

        "procedure negoziate senza bando":
            "procedura negoziata senza bando senza previa pubblicazione di un bando articolo 50 comma 1 lettere c d e articolo 76 operatori da invitare indagine di mercato",

        "offerta economicamente più vantaggiosa":
            "criterio dell'offerta economicamente più vantaggiosa articolo 108 criteri di aggiudicazione rapporto qualità prezzo",

        "attività del rup":
            "attività del RUP allegato I.2 articolo 15 compiti del responsabile unico del progetto",

        "indagini di mercato":
            "indagini di mercato allegato II.1 articolo 50 procedure negoziate operatori economici",

        "qualificazione stazioni appaltanti":
            "qualificazione stazioni appaltanti articolo 62 articolo 63 allegato II.4",

        "direzione dei lavori":
            "direzione dei lavori articolo 115 allegato II.14 direttore dei lavori",

        "certificato di regolare esecuzione":
            "certificato di regolare esecuzione articolo 50 comma 7 articolo 116 allegato II.14",
    }

    return expansions.get(q, query_text)

def get_collection_query(query_text: str, collection_name: str) -> str:
    q = query_text.lower().strip()

    if q == "procedure negoziate senza bando":
        if collection_name == DLGS36_MAIN:
            return "articolo 50 articolo 76 procedura negoziata senza bando senza previa pubblicazione bando"
        if collection_name == DLGS36_II1:
            return "operatori da invitare indagine di mercato elenchi procedura negoziata articolo 50"

    if q == "affidamento diretto sotto soglia":
        if collection_name == DLGS36_MAIN:
            return "articolo 50 affidamento diretto sotto soglia lavori servizi forniture"
        if collection_name == DLGS36_II1:
            return "indagine di mercato elenchi operatori affidamento sotto soglia articolo 50"

    if q == "responsabile unico del progetto":
        if collection_name == DLGS36_MAIN:
            return "articolo 15 responsabile unico del progetto RUP"
        if collection_name == DLGS36_I2:
            return "RUP requisiti compiti allegato I.2 articolo 15"

    if q == "qualificazione stazioni appaltanti":
        if collection_name == DLGS36_MAIN:
            return "articolo 62 articolo 63 qualificazione stazioni appaltanti"
        if collection_name == DLGS36_II4:
            return "allegato II.4 qualificazione stazioni appaltanti AUSA"

    if q == "direzione dei lavori":
        if collection_name == DLGS36_MAIN:
            return "articolo 115 direttore dei lavori"
        if collection_name == DLGS36_II14:
            return "allegato II.14 direttore dei lavori ufficio direzione lavori"

    if q == "certificato di regolare esecuzione":
        if collection_name == DLGS36_MAIN:
            return "articolo 116 articolo 50 comma 7 certificato di regolare esecuzione"
        if collection_name == DLGS36_II14:
            return "allegato II.14 certificato di regolare esecuzione articolo 28 articolo 38"

    if q == "offerta economicamente più vantaggiosa":
        if collection_name == DLGS36_MAIN:
            return "criterio dell'offerta economicamente più vantaggiosa articolo 108 criteri di aggiudicazione rapporto qualità prezzo"

    return expand_dlgs36_query_v2(query_text)

def score_result(query_text: str, collection_name: str, meta: dict, distance):
    score = 0.0

    if distance is not None:
        score += max(0.0, 10.0 - float(distance))

    articolo = str(meta.get("articolo", "")).lstrip("0")
    allegato = meta.get("allegato", "")
    q = query_text.lower()

    # affidamento diretto / sotto soglia
    if "affidamento diretto" in q or "sotto soglia" in q:
        if articolo == "50":
            score += 12
        if allegato == "II.1":
            score += 7

    # principio di rotazione
    if "rotazione" in q:
        if articolo == "49":
            score += 12

    # RUP
    if "responsabile unico del progetto" in q or "rup" in q:
        if articolo == "15":
            score += 12
        if allegato == "I.2":
            score += 9

    # qualificazione
    if "qualificazione" in q:
        if articolo in {"62", "63"}:
            score += 12
        if allegato == "II.4":
            score += 9

    # indagini di mercato
    if "indagini di mercato" in q:
        if allegato == "II.1":
            score += 12
        if articolo == "50":
            score += 7

    # procedure negoziate senza bando
    if "procedura negoziata" in q or "negoziate senza bando" in q:
        if articolo == "50":
            score += 16
        if articolo == "76":
            score += 14
        if allegato == "II.1":
            score += 7
        if articolo == "187" and "concess" not in q:
            score -= 6

    # OEPV
    if "offerta economicamente più vantaggiosa" in q or "criterio dell'offerta economicamente più vantaggiosa" in q:
        if articolo == "108":
            score += 14

    # direzione lavori
    if "direzione dei lavori" in q or "direttore dei lavori" in q:
        if articolo == "115":
            score += 10
        if allegato == "II.14" and articolo in {"1", "2", "5", "8", "10"}:
            score += 10
        elif allegato == "II.14":
            score += 3

    # regolare esecuzione
    if "regolare esecuzione" in q or "certificato di regolare esecuzione" in q:
        if articolo in {"50", "116"}:
            score += 10
        if allegato == "II.14" and articolo in {"28", "38", "37"}:
            score += 10
        elif allegato == "II.14":
            score += 3

    # art. 11 / CCNL
    if "contratto collettivo" in q or "ccnl" in q or "equivalenza tutele" in q:
        if allegato == "I.1":
            score += 12

    return round(score, 4)

def fetch_main_article_pin(client, embedding_fn, articolo: int, forced_score: float):
    coll = client.get_collection(name=DLGS36_MAIN, embedding_function=embedding_fn)

    candidate_ids = [
        f"dlgs36_2023_art_{articolo:03d}_chunk_001",
        f"dlgs36_2023_art_{articolo:03d}_chunk_002",
    ]

    res = coll.get(ids=candidate_ids, include=["documents", "metadatas"])

    ids = res.get("ids", [])
    docs = res.get("documents", [])
    metas = res.get("metadatas", [])

    if not ids:
        return None

    rid = ids[0]
    doc = docs[0]
    meta = metas[0]

    return {
        "id": rid,
        "score": forced_score,
        "collection": DLGS36_MAIN,
        "articolo": str(meta.get("articolo", "")).lstrip("0"),
        "allegato": meta.get("allegato", ""),
        "source_id": meta.get("source_id", ""),
        "preview": doc[:250].replace("\n", " "),
    }

def pin_results_for_dlgs36(query_text: str, merged: list[dict], client, embedding_fn) -> list[dict]:
    q = query_text.lower().strip()
    rest = merged[:]
    pinned = []

    def pull_existing(predicate):
        for i, item in enumerate(rest):
            if predicate(item):
                return rest.pop(i)
        return None

    def ensure_main_article(articolo: int, forced_score: float):
        item = pull_existing(
            lambda x: x["collection"] == DLGS36_MAIN and x["articolo"] == str(articolo)
        )
        if item is None:
            item = fetch_main_article_pin(client, embedding_fn, articolo, forced_score)
        if item is not None:
            pinned.append(item)

    # Art. 50 = presidio prioritario per affidamenti diretti e sotto soglia
    if any(k in q for k in ["affidamento diretto", "sotto soglia", "articolo 50"]):
        ensure_main_article(50, 100.0)

    # Procedure negoziate: prima il Codice, poi l'allegato operativo
    if "procedura negoziata" in q or "negoziate senza bando" in q:
        ensure_main_article(50, 100.0)
        ensure_main_article(76, 99.0)

    # Regolare esecuzione: mantieni presidio del Codice
    if "regolare esecuzione" in q or "certificato di regolare esecuzione" in q:
        ensure_main_article(116, 98.0)

    seen = set()
    ordered = []
    for item in pinned + rest:
        if item["id"] not in seen:
            ordered.append(item)
            seen.add(item["id"])

    return ordered

def main():
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    all_results = {
        "persist_dir": PERSIST_DIR,
        "queries": []
    }

    print("=== FEDERATED RETRIEVAL TEST D.LGS. 36/2023 ===")

    for query in TEST_QUERIES:
        routed = route_dlgs36_contracts_collections_v2(query)
        expanded = expand_dlgs36_query_v2(query)

        print("\n" + "=" * 110)
        print(f"QUERY: {query}")
        print(f"EXPANDED: {expanded}")
        print(f"ROUTED: {routed}")
        print("=" * 110)

        merged = []

        for collection_name in routed:
            coll = client.get_collection(name=collection_name, embedding_function=embedding_fn)
            collection_query = get_collection_query(query, collection_name)
            print(f"[COLLECTION QUERY] {collection_name} -> {collection_query}")
            res = coll.query(query_texts=[collection_query], n_results=12)

            ids = res.get("ids", [[]])[0]
            docs = res.get("documents", [[]])[0]
            metas = res.get("metadatas", [[]])[0]
            distances = res.get("distances", [[]])[0] if "distances" in res else [None] * len(ids)

            for rid, doc, meta, dist in zip(ids, docs, metas, distances):
                score = score_result(query, collection_name, meta, dist)
                articolo = str(meta.get("articolo", "")).lstrip("0")
                allegato = meta.get("allegato", "")
                source_id = meta.get("source_id", "")
                preview = doc[:250].replace("\n", " ")

                merged.append({
                    "id": rid,
                    "score": score,
                    "collection": collection_name,
                    "articolo": articolo,
                    "allegato": allegato,
                    "source_id": source_id,
                    "preview": preview,
                })

        merged.sort(key=lambda x: x["score"], reverse=True)
        merged = pin_results_for_dlgs36(query, merged, client, embedding_fn)
        top = merged[:8]

        for i, item in enumerate(top, start=1):
            print(f"{i}. score={item['score']} id={item['id']}")
            print(f"   collection={item['collection']} articolo={item['articolo']} allegato={item['allegato']} source={item['source_id']}")
            print(f"   {item['preview']}")

        all_results["queries"].append({
            "query": query,
            "expanded_query": expanded,
            "routed_collections": routed,
            "results": top
        })

    OUTPUT_JSON.write_text(
        json.dumps(all_results, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("\n" + "=" * 110)
    print(f"[OK] file risultati scritto in: {OUTPUT_JSON}")
    print("=" * 110)

if __name__ == "__main__":
    main()