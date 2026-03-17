from pathlib import Path
import json
import chromadb
from chromadb.utils import embedding_functions

PERSIST_DIR = "data/chroma"
OUTPUT_JSON = Path("data/processed/retrieval_tests/router_federato_generale_base_results.json")

DLGS36_MAIN = "normattiva_dlgs36_2023_articles"
DLGS36_I1 = "normattiva_dlgs36_2023_all_i1"
DLGS36_I2 = "normattiva_dlgs36_2023_all_i2"
DLGS36_II1 = "normattiva_dlgs36_2023_all_ii1"
DLGS36_II4 = "normattiva_dlgs36_2023_all_ii4"
DLGS36_II14 = "normattiva_dlgs36_2023_all_ii14"

TUEL_MAIN = "normattiva_tuel_267_2000"
L241_MAIN = "normattiva_l241_1990"

DLGS118_MAIN = "normattiva_dlgs118_2011_main"
DLGS118_ALL_1 = "normattiva_dlgs118_2011_all_1"
DLGS118_ALL_4_1 = "normattiva_dlgs118_2011_all_4_1"

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
    "fondo di riserva",
    "debiti fuori bilancio",
    "equilibri di bilancio",
    "annullamento d'ufficio",
    "responsabile del procedimento",
]

def list_collection_names(client) -> list[str]:
    names = []
    for item in client.list_collections():
        if isinstance(item, str):
            names.append(item)
        else:
            names.append(item.name)
    return names

def unique_keep_order(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for x in items:
        if x and x not in seen:
            out.append(x)
            seen.add(x)
    return out

def safe_collection_exists(collection_name: str | None, available: set[str]) -> bool:
    return bool(collection_name) and collection_name in available

def route_domains(query_text: str) -> list[str]:
    q = query_text.lower().strip()
    domains = []

    if any(k in q for k in [
        "affidamento diretto",
        "sotto soglia",
        "articolo 50",
        "procedura negoziata",
        "procedure negoziate",
        "negoziata senza bando",
        "negoziate senza bando",
        "senza bando",
        "rotazione",
        "rup",
        "responsabile unico del progetto",
        "indagini di mercato",
        "stazione appaltante qualificata",
        "qualificazione stazioni appaltanti",
        "direzione dei lavori",
        "direttore dei lavori",
        "regolare esecuzione",
        "certificato di regolare esecuzione",
        "offerta economicamente più vantaggiosa",
    ]):
        domains.append("dlgs36")

    if any(k in q for k in [
        "fondo di riserva",
        "debiti fuori bilancio",
        "equilibri di bilancio",
        "consiglio comunale",
        "giunta",
        "pareri ex art. 49",
        "articolo 49 tuel",
        "articolo 166",
        "articolo 176",
        "articolo 193",
        "articolo 194",
    ]):
        domains.append("tuel")

    if any(k in q for k in [
        "annullamento d'ufficio",
        "autotutela",
        "responsabile del procedimento",
        "accesso agli atti",
        "conferenza di servizi",
        "silenzio assenso",
        "motivazione del provvedimento",
        "partecipazione al procedimento",
    ]):
        domains.append("l241")

    if any(k in q for k in [
        "equilibri di bilancio",
        "competenza finanziaria potenziata",
        "fpv",
        "fondo pluriennale vincolato",
        "principio contabile",
        "allegato 4/1",
        "programmazione",
        "bilancio armonizzato",
    ]):
        domains.append("dlgs118")

    if not domains:
        domains = ["tuel", "l241", "dlgs36", "dlgs118"]

    return unique_keep_order(domains)

def get_domain_collections(domain: str, query_text: str | None = None) -> list[str | None]:
    q = (query_text or "").lower().strip()

    if domain == "dlgs36":
        if any(k in q for k in ["affidamento diretto", "sotto soglia", "indagini di mercato"]):
            return [DLGS36_MAIN, DLGS36_II1]

        if any(k in q for k in ["procedura negoziata", "procedure negoziate", "negoziata senza bando", "negoziate senza bando", "senza bando"]):
            return [DLGS36_MAIN, DLGS36_II1]

        if any(k in q for k in ["responsabile unico del progetto", "attività del rup", "rup"]):
            return [DLGS36_MAIN, DLGS36_I2]

        if "qualificazione stazioni appaltanti" in q or "stazione appaltante qualificata" in q:
            return [DLGS36_MAIN, DLGS36_II4]

        if any(k in q for k in ["direzione dei lavori", "direttore dei lavori"]):
            return [DLGS36_MAIN, DLGS36_II14]

        if any(k in q for k in ["regolare esecuzione", "certificato di regolare esecuzione"]):
            return [DLGS36_MAIN, DLGS36_II14]

        if "offerta economicamente più vantaggiosa" in q:
            return [DLGS36_MAIN]

        return [DLGS36_MAIN, DLGS36_I2, DLGS36_II1, DLGS36_II4, DLGS36_II14]

    mapping = {
        "tuel": [TUEL_MAIN],
        "l241": [L241_MAIN],
        "dlgs118": [DLGS118_MAIN, DLGS118_ALL_1, DLGS118_ALL_4_1],
    }
    return mapping.get(domain, [])

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

def get_dlgs36_collection_query(query_text: str, collection_name: str) -> str:
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

    if q == "attività del rup":
        if collection_name == DLGS36_MAIN:
            return "articolo 15 responsabile unico del progetto RUP"
        if collection_name == DLGS36_I2:
            return "compiti del RUP allegato I.2 articolo 6 articolo 15"

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

    if q == "offerta economicamente più vantaggiosa" and collection_name == DLGS36_MAIN:
        return "criterio dell'offerta economicamente più vantaggiosa articolo 108 criteri di aggiudicazione rapporto qualità prezzo"

    return expand_dlgs36_query_v2(query_text)

def score_dlgs36_result(query_text: str, meta: dict, distance):
    score = 0.0
    if distance is not None:
        score += max(0.0, 10.0 - float(distance))

    articolo = str(meta.get("articolo", "")).lstrip("0")
    allegato = meta.get("allegato", "")
    q = query_text.lower()

    if "affidamento diretto" in q or "sotto soglia" in q:
        if articolo == "50":
            score += 12
        if allegato == "II.1":
            score += 7

    if "rotazione" in q and articolo == "49":
        score += 12

    if "responsabile unico del progetto" in q or "rup" in q:
        if articolo == "15":
            score += 12
        if allegato == "I.2":
            score += 9

    if "qualificazione" in q:
        if articolo in {"62", "63"}:
            score += 12
        if allegato == "II.4":
            score += 9

    if "indagini di mercato" in q:
        if allegato == "II.1":
            score += 12
        if articolo == "50":
            score += 7

    if "procedura negoziata" in q or "procedure negoziate" in q or "negoziata senza bando" in q or "negoziate senza bando" in q:
        if articolo == "50":
            score += 16
        if articolo == "76":
            score += 14
        if allegato == "II.1":
            score += 7
        if articolo == "187" and "concess" not in q:
            score -= 6

    if "offerta economicamente più vantaggiosa" in q or "criterio dell'offerta economicamente più vantaggiosa" in q:
        if articolo == "108":
            score += 14

    if "direzione dei lavori" in q or "direttore dei lavori" in q:
        if articolo == "115":
            score += 10
        if allegato == "II.14" and articolo in {"1", "2", "5", "8", "10"}:
            score += 10
        elif allegato == "II.14":
            score += 3

    if "regolare esecuzione" in q or "certificato di regolare esecuzione" in q:
        if articolo in {"50", "116"}:
            score += 10
        if allegato == "II.14" and articolo in {"28", "38", "37"}:
            score += 10
        elif allegato == "II.14":
            score += 3

    return round(score, 4)

def fetch_dlgs36_main_article_pin(client, embedding_fn, articolo: int, forced_score: float):
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
        "domain": "dlgs36",
        "collection": DLGS36_MAIN,
        "articolo": str(meta.get("articolo", "")).lstrip("0"),
        "allegato": meta.get("allegato", ""),
        "source_id": meta.get("source_id", ""),
        "preview": doc[:250].replace("\n", " "),
    }

def pin_dlgs36_results(query_text: str, merged: list[dict], client, embedding_fn) -> list[dict]:
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
            item = fetch_dlgs36_main_article_pin(client, embedding_fn, articolo, forced_score)
        if item is not None:
            item["domain"] = "dlgs36"
            pinned.append(item)

    if any(k in q for k in ["affidamento diretto", "sotto soglia", "articolo 50"]):
        ensure_main_article(50, 100.0)

    if "procedura negoziata" in q or "procedure negoziate" in q or "negoziata senza bando" in q or "negoziate senza bando" in q:
        ensure_main_article(50, 100.0)
        ensure_main_article(76, 99.0)

    if "regolare esecuzione" in q or "certificato di regolare esecuzione" in q:
        ensure_main_article(116, 98.0)

    seen = set()
    ordered = []
    for item in pinned + rest:
        if item["id"] not in seen:
            ordered.append(item)
            seen.add(item["id"])
    return ordered

def generic_query_for_domain(query_text: str, domain: str, collection_name: str) -> str:
    q = query_text.lower().strip()

    if domain == "tuel":
        if "fondo di riserva" in q:
            return "articolo 166 articolo 176 fondo di riserva prelevamenti"
        if "debiti fuori bilancio" in q:
            return "articolo 194 debiti fuori bilancio riconoscimento legittimità"
        if "equilibri di bilancio" in q:
            return "articolo 193 equilibri di bilancio salvaguardia"
        return query_text

    if domain == "l241":
        if "annullamento d'ufficio" in q:
            return "annullamento d'ufficio articolo 21 nonies"
        if "responsabile del procedimento" in q:
            return "responsabile del procedimento articolo 4 articolo 5 articolo 6"
        return query_text

    if domain == "dlgs118":
        if "equilibri di bilancio" in q:
            return "equilibri di bilancio decreto legislativo 118 2011 principio contabile armonizzato allegato 4/2 allegato 4/1"
        if "fpv" in q or "fondo pluriennale vincolato" in q:
            return "fondo pluriennale vincolato principio contabile allegato 4/2"
        return query_text

    return query_text

def generic_score(domain: str, query_text: str, meta: dict, distance):
    score = 0.0
    if distance is not None:
        score += max(0.0, 10.0 - float(distance))

    articolo = str(meta.get("articolo", "")).lstrip("0")
    allegato = meta.get("allegato", "")
    q = query_text.lower()

    if domain == "tuel":
        if "fondo di riserva" in q and articolo in {"166", "176"}:
            score += 12
        if "debiti fuori bilancio" in q and articolo == "194":
            score += 12
        if "equilibri di bilancio" in q and articolo == "193":
            score += 12

    if domain == "l241":
        if "annullamento d'ufficio" in q and ("21" in articolo or "nonies" in articolo):
            score += 12
        if "responsabile del procedimento" in q:
            if articolo == "4":
                score += 14
            elif articolo == "5":
                score += 13
            elif articolo == "6":
                score += 12

    if domain == "dlgs118":
        if "equilibri di bilancio" in q:
            if allegato in {"4.1", "4/1", "1"}:
                score += 8
            if allegato in {"4.2", "4/2"}:
                score += 10
        if "fpv" in q or "fondo pluriennale vincolato" in q:
            score += 10

    return round(score, 4)

def fetch_l241_article_pin(client, embedding_fn, articolo_id_fragment: str, forced_score: float):
    coll = client.get_collection(name=L241_MAIN, embedding_function=embedding_fn)

    candidate_ids = [
        f"l241_1990_art_{articolo_id_fragment}_001",
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
        "domain": "l241",
        "collection": L241_MAIN,
        "articolo": str(meta.get("articolo", "")).lstrip("0"),
        "allegato": meta.get("allegato", ""),
        "source_id": meta.get("source_id", ""),
        "preview": doc[:250].replace("\n", " "),
    }

def pin_l241_results(query_text: str, merged: list[dict], client, embedding_fn) -> list[dict]:
    q = query_text.lower().strip()
    rest = merged[:]
    pinned = []

    def pull_existing(predicate):
        for i, item in enumerate(rest):
            if predicate(item):
                return rest.pop(i)
        return None

    def ensure_l241_article(articolo_id_fragment: str, forced_score: float):
        target_id = f"l241_1990_art_{articolo_id_fragment}_001"

        item = pull_existing(lambda x: x["id"] == target_id)
        if item is None:
            item = fetch_l241_article_pin(client, embedding_fn, articolo_id_fragment, forced_score)
        if item is not None:
            item["domain"] = "l241"
            pinned.append(item)

    if "annullamento d'ufficio" in q:
        ensure_l241_article("21_novies", 100.0)

    if "responsabile del procedimento" in q:
        ensure_l241_article("4", 100.0)
        ensure_l241_article("5", 99.0)
        ensure_l241_article("6", 98.0)

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

    available = set(list_collection_names(client))

    print("=== ROUTER FEDERATO GENERALE – BASE ===")
    print("Collections disponibili:")
    for name in sorted(available):
        print(f"- {name}")

    all_results = {
        "persist_dir": PERSIST_DIR,
        "available_collections": sorted(available),
        "queries": []
    }

    for query in TEST_QUERIES:
        domains = route_domains(query)

        print("\n" + "=" * 110)
        print(f"QUERY: {query}")
        print(f"DOMAINS: {domains}")
        print("=" * 110)

        merged = []

        for domain in domains:
            raw_collections = get_domain_collections(domain, query)
            active_collections = [c for c in raw_collections if safe_collection_exists(c, available)]

            print(f"[DOMAIN] {domain} -> {active_collections}")

            for collection_name in active_collections:
                coll = client.get_collection(name=collection_name, embedding_function=embedding_fn)

                if domain == "dlgs36":
                    collection_query = get_dlgs36_collection_query(query, collection_name)
                else:
                    collection_query = generic_query_for_domain(query, domain, collection_name)

                print(f"[COLLECTION QUERY] {collection_name} -> {collection_query}")

                res = coll.query(query_texts=[collection_query], n_results=12)

                ids = res.get("ids", [[]])[0]
                docs = res.get("documents", [[]])[0]
                metas = res.get("metadatas", [[]])[0]
                distances = res.get("distances", [[]])[0] if "distances" in res else [None] * len(ids)

                for rid, doc, meta, dist in zip(ids, docs, metas, distances):
                    if domain == "dlgs36":
                        score = score_dlgs36_result(query, meta, dist)
                    else:
                        score = generic_score(domain, query, meta, dist)

                    articolo = str(meta.get("articolo", "")).lstrip("0")
                    allegato = meta.get("allegato", "")
                    source_id = meta.get("source_id", "")
                    preview = doc[:250].replace("\n", " ")

                    merged.append({
                        "id": rid,
                        "score": score,
                        "domain": domain,
                        "collection": collection_name,
                        "articolo": articolo,
                        "allegato": allegato,
                        "source_id": source_id,
                        "preview": preview,
                    })

        merged.sort(key=lambda x: x["score"], reverse=True)

        if "dlgs36" in domains:
            merged = pin_dlgs36_results(query, merged, client, embedding_fn)

        if "l241" in domains:
            merged = pin_l241_results(query, merged, client, embedding_fn)

        top = merged[:10]

        for i, item in enumerate(top, start=1):
            print(f"{i}. score={item['score']} id={item['id']}")
            print(
                f"   domain={item['domain']} collection={item['collection']} "
                f"articolo={item['articolo']} allegato={item['allegato']} source={item['source_id']}"
            )
            print(f"   {item['preview']}")

        all_results["queries"].append({
            "query": query,
            "domains": domains,
            "results": top
        })

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(all_results, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("\n" + "=" * 110)
    print(f"[OK] file risultati scritto in: {OUTPUT_JSON}")
    print("=" * 110)

if __name__ == "__main__":
    main()