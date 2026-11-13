
"""
Preliminary RAG retrieval quality evaluation.

Ground-truth mappings are provisional and
require educational validation.
"""

from retrieval import load_knowledge_base, retrieve_chunks
import json
from pathlib import Path


DATA_PATH = Path(__file__).resolve().parent / "rag_source_data.json"

# Provisional curriculum-based relevance labels.
# All listed IDs are required for complete coverage.
GROUND_TRUTH = {
    "Q01": ["C02", "C05"],
    "Q02": ["C03"],
    "Q03": ["C04"],
    "Q04": ["C05"],
    "Q05": ["C06"],
    "Q06": ["C06"],
    "Q07": ["C08"],
    "Q08": ["C09"],
    "Q09": ["C04", "C09"],
    "Q10": ["C11"],
    "Q11": ["C04", "C09"],
    "Q12": ["C11"],
}


def evaluate_retrieval(top_k=3):
    with DATA_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    queries = data["queries"]
    available_ids = {
        node["node_id"] for node in load_knowledge_base()
    }

    assert len(queries) == len(GROUND_TRUTH)

    results = []

    for item in queries:
        query_id = item["query_id"]
        query_text = item["query_ar"]

        relevant = set(GROUND_TRUTH[query_id])

        if not relevant.issubset(available_ids):
            raise ValueError(
                f"Invalid ground truth for {query_id}"
            )

        retrieved = retrieve_chunks(
            query_text,
            top_k=top_k
        )

        retrieved_ids = [
            chunk["node_id"] for chunk in retrieved
        ]

        matches = relevant.intersection(retrieved_ids)

        hit = int(bool(matches))
        recall = len(matches) / len(relevant)
        complete = int(relevant.issubset(set(retrieved_ids)))

        reciprocal_rank = 0.0

        for rank, node_id in enumerate(retrieved_ids, 1):
            if node_id in relevant:
                reciprocal_rank = 1 / rank
                break

        results.append({
            "query_id": query_id,
            "retrieved": retrieved_ids,
            "relevant": sorted(relevant),
            "hit": hit,
            "recall": recall,
            "complete": complete,
            "rr": reciprocal_rank,
        })

    n = len(results)

    print("\n=== RAG RETRIEVAL QUALITY ===")

    for result in results:
        print(
            f"{result['query_id']} | "
            f"Retrieved: {result['retrieved']} | "
            f"Expected: {result['relevant']} | "
            f"Recall: {result['recall']:.2f}"
        )

    print("\n=== SUMMARY ===")
    print(f"Hit@{top_k}: "
          f"{sum(r['hit'] for r in results) / n:.3f}")
    print(f"Recall@{top_k}: "
          f"{sum(r['recall'] for r in results) / n:.3f}")
    print(f"Complete@{top_k}: "
          f"{sum(r['complete'] for r in results) / n:.3f}")
    print(f"MRR@{top_k}: "
          f"{sum(r['rr'] for r in results) / n:.3f}")

    print("\nEvaluation completed successfully.")


if __name__ == "__main__":
    evaluate_retrieval(top_k=3)
