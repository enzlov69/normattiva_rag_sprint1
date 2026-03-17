import json
from rag_retriever import query_rag

TEST_FILE = "test_queries_dlgs118_final.json"

def run_tests():

    with open(TEST_FILE, "r", encoding="utf-8") as f:
        tests = json.load(f)

    results = []

    for t in tests:

        query = t["query"]
        test_id = t["test_id"]

        retrieval = query_rag(query, top_k=5)

        top_sources = [r["source_collection"] for r in retrieval]

        result = {
            "test_id": test_id,
            "query": query,
            "top_sources": top_sources
        }

        results.append(result)

        print("\nTEST:", test_id)
        print("QUERY:", query)
        print("TOP SOURCES:", top_sources)

    with open("dlgs118_test_results.json","w",encoding="utf-8") as f:
        json.dump(results,f,indent=2)

if __name__ == "__main__":
    run_tests()