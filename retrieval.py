
import json
from pathlib import Path
from functools import lru_cache

import numpy as np
import faiss

from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer


DATA_PATH = Path(__file__).resolve().parent / "rag_source_data.json"

MODEL_NAME = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

RRF_K = 60


@lru_cache(maxsize=1)
def load_knowledge_base():
    with DATA_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    nodes = data["nodes"]

    if not nodes:
        raise ValueError("Knowledge base is empty.")

    return nodes


@lru_cache(maxsize=1)
def build_retrieval_index():
    nodes = load_knowledge_base()

    texts = [node["text"] for node in nodes]

    # Semantic embeddings
    model = SentenceTransformer(MODEL_NAME)

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    ).astype("float32")

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    # Character-level lexical retrieval
    vectorizer = TfidfVectorizer(
        analyzer="char",
        ngram_range=(2, 5),
        sublinear_tf=True
    )

    tfidf_matrix = vectorizer.fit_transform(texts)

    return nodes, model, index, vectorizer, tfidf_matrix


def retrieve_chunks(query, top_k=3):
    if not isinstance(top_k, int) or top_k < 1:
        raise ValueError("top_k must be a positive integer.")

    if not isinstance(query, str) or not query.strip():
        return []

    (
        nodes,
        model,
        index,
        vectorizer,
        tfidf_matrix
    ) = build_retrieval_index()

    count = len(nodes)

    # 1. Semantic retrieval with FAISS
    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    ).astype("float32")

    _, semantic_indices = index.search(
        query_embedding,
        count
    )

    semantic_ranking = semantic_indices[0].tolist()

    # 2. Lexical retrieval with TF-IDF
    query_tfidf = vectorizer.transform([query])

    lexical_scores = (
        tfidf_matrix @ query_tfidf.T
    ).toarray().ravel()

    lexical_ranking = np.argsort(
        -lexical_scores,
        kind="stable"
    ).tolist()

    # 3. Reciprocal Rank Fusion
    fused_scores = {}

    
# Selected configuration from retrieval evaluation
SEMANTIC_WEIGHT = 0.2
LEXICAL_WEIGHT = 0.8

for weight, ranking in [
    (SEMANTIC_WEIGHT, semantic_ranking),
    (LEXICAL_WEIGHT, lexical_ranking)
]:
    for rank, node_index in enumerate(ranking, start=1):
        fused_scores[node_index] = (
            fused_scores.get(node_index, 0.0)
            + weight / (RRF_K + rank)
        )


    sorted_indices = sorted(
        fused_scores,
        key=lambda i: (-fused_scores[i], i)
    )

    results = []

    for i in sorted_indices[:top_k]:
        node = nodes[i]
        metadata = node.get("metadata", {})
        provenance = metadata.get("provenance", {})

        results.append({
            "node_id": node["node_id"],
            "text": node["text"],
            "page_numbers": provenance.get(
                "page_numbers", []
            ),
            "score": fused_scores[i],
            "metadata": metadata
        })

    return results


if __name__ == "__main__":
    question = (
        "ماذا يحدث للمادة الوراثية DNA "
        "قبل انقسام الخلية؟"
    )

    results = retrieve_chunks(question, top_k=3)

    for result in results:
        print(
            result["node_id"],
            result["score"]
        )
