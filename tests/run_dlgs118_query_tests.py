import json
from pathlib import Path

QUERY_FILE = Path("data/test_queries/test_queries_dlgs118_final.json")

def main():

    if not QUERY_FILE.exists():
        print("File query NON trovato:", QUERY_FILE)
        return

    with open(QUERY_FILE, "r", encoding="utf-8") as f:
        queries = json.load(f)

    print("=== PACCHETTO TEST DLGS 118 ===")

    for q in queries:
        print("\nTEST:", q["test_id"])
        print("AREA:", q.get("area"))
        print("QUERY:", q["query"])
        print("EXPECTED:", q.get("expected_primary"))

    print("\nTotale query:", len(queries))


if __name__ == "__main__":
    main()