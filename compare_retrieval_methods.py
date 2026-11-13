
"""
Compare Semantic, Lexical, and Hybrid retrieval.

Uses the same provisional relevance labels
as test_retrieval_quality.py.

Evaluation is preliminary, not independently validated.
"""

import numpy as np

from retrieval import (
    build_retrieval_index,
    load_knowledge_base,
    RRF_K,
    SEMANTIC_WEIGHT,
    LEXICAL_WEIGHT,
)

from test_retrieval_quality import GROUND_TRUTH
import json
from pathlib import Path


DATA_PATH = Path(__file__).resolve().parent / "rag_source_data.json"
TOP_K = 3


def get_rankings(query):
    nodes, model, index, vectorizer, tfidf_matrix = (
        build_retrieval_index()
    )

    count = len(nodes)

    embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype("float32")

    _, semantic_indices = index.search(embedding, count)

    semantic = semantic_indices[0].tolist()

    lexical_scores = (
        tfidf_matrix @ vectorizer.transform([query]).T
    ).toarray().ravel()

    lexical = np.argsort(
        -lexical_scores,
        kind="stable"
    ).tolist()

    fused_scores = {}

    for weight, ranking in [
        (SEMANTIC_WEIGHT, semantic),
        (LEXICAL_WEIGHT, lexical),
    ]:
        for rank, node_index in enumerate(ranking, start=1):
            fused_scores[node_index] = (
                fused_scores.get(node_index, 0.0)
                + weight / (RRF_K + rank)
            )

    hybrid = sorted(
        fused_scores,
        key=lambda i: (-fused_scores[i], i)
    )

    return {
        "Semantic": [
            nodes[i].node_id for i in semantic[:TOP_K]
        ],
        "Lexical": [
            nodes[i].node_id for i in lexical[:TOP_K]
        ],
        "Hybrid": [
            nodes[i].node_id for i in hybrid[:TOP_K]
        ],
    }


def evaluate(ids, relevant):
    relevant = set(relevant)
    retrieved = set(ids)

    matches = relevant & retrieved

    hit = int(bool(matches))
    recall = len(matches) / len(relevant)
    complete = int(relevant.issubset(retrieved))

    rr = 0.0

    for rank, node_id in enumerate(ids, start=1):
        if node_id in relevant:
            rr = 1.0 / rank
            break

    return hit, recall, complete, rr


def main():
    with DATA_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    queries = data["queries"]

    available_ids = {
        node["node_id"] for node in load_knowledge_base()
    }

    assert len(queries) == len(GROUND_TRUTH)

    scores = {
        method: []
        for method in ["Semantic", "Lexical", "Hybrid"]
    }

    for item in queries:
        query_id = item["query_id"]
        query_text = item["query_ar"]

        relevant = GROUND_TRUTH[query_id]

        if not set(relevant).issubset(available_ids):
            raise ValueError(
                f"Invalid ground truth for {query_id}"
            )

        rankings = get_rankings(query_text)

        print(f"\n{query_id}: {query_text}")

        for method, ids in rankings.items():
            metrics = evaluate(ids, relevant)
            scores[method].append(metrics)

            print(
                f"  {method}: {ids} | "
                f"Recall@3={metrics[1]:.2f}"
            )

    print("\n=== METHOD COMPARISON ===")

    for method, results in scores.items():
        averages = np.mean(results, axis=0)

        print(f"\n{method}")
        print(f"Hit@3: {averages[0]:.3f}")
        print(f"Recall@3: {averages[1]:.3f}")
        print(f"Complete@3: {averages[2]:.3f}")
        print(f"MRR@3: {averages[3]:.3f}")

    print("\nComparison completed successfully.")


if __name__ == "__main__":
    main()
