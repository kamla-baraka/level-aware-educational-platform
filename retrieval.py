
import json
import re
from pathlib import Path


DATA_PATH = Path(__file__).resolve().parent / "rag_source_data.json"

# Common Arabic words that add little value to keyword retrieval.
STOPWORDS = {
    "في", "من", "إلى", "على", "عن", "ما", "ماذا", "كيف",
    "هل", "هو", "هي", "هذا", "هذه", "ذلك", "التي",
    "الذي", "و", "أو", "ثم", "أن", "إن", "كل", "عند",
    "عدد", "بين", "مع", "خلال", "بعد", "قبل"
}


def load_knowledge_base():
    """Load curriculum chunks from the JSON knowledge base."""
    with DATA_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    nodes = data.get("nodes", [])

    if not nodes:
        raise ValueError("No curriculum nodes found in the JSON file.")

    return nodes


def normalize_arabic(text):
    """Normalize Arabic text for basic keyword matching."""
    text = str(text).lower()

    # Remove Arabic diacritics.
    text = re.sub(r"[\u064b-\u065f\u0670]", "", text)

    # Normalize common letter variants.
    text = re.sub(r"[إأآٱ]", "ا", text)
    text = text.replace("ى", "ي")
    text = text.replace("ؤ", "و")
    text = text.replace("ئ", "ي")
    text = text.replace("ـ", "")

    # Keep Arabic letters, Latin letters, and numbers.
    text = re.sub(r"[^\u0621-\u064aa-z0-9\s]", " ", text)

    return " ".join(text.split())


def tokenize(text):
    """Extract useful search tokens."""
    normalized = normalize_arabic(text)

    return [
        word
        for word in normalized.split()
        if len(word) > 1 and word not in STOPWORDS
    ]


def calculate_relevance(query, node):
    """Calculate a simple keyword-overlap relevance score."""
    query_tokens = set(tokenize(query))

    if not query_tokens:
        return 0.0

    content = node.get("text", "")

    metadata = node.get("metadata", {})
    provenance = metadata.get("provenance", {})
    pedagogical = metadata.get("pedagogical", {})

    topic = provenance.get("topic_label", "")
    concepts = pedagogical.get("core_concepts", [])

    content_tokens = set(tokenize(content))
    metadata_tokens = set(tokenize(
        topic + " " + " ".join(concepts)
    ))

    content_matches = len(query_tokens & content_tokens)
    metadata_matches = len(query_tokens & metadata_tokens)

    # Give extra weight to matching curriculum concepts.
    return float(content_matches + 2 * metadata_matches)


def retrieve_chunks(query, top_k=3):
    """
    Retrieve the most relevant curriculum chunks.

    Returns a list with source IDs, page numbers,
    relevance scores, and source text.
    """
    if not isinstance(top_k, int) or top_k < 1:
        raise ValueError("top_k must be a positive integer.")

    if not query or not query.strip():
        return []

    nodes = load_knowledge_base()
    results = []

    for node in nodes:
        score = calculate_relevance(query, node)

        if score <= 0:
            continue

        metadata = node.get("metadata", {})
        provenance = metadata.get("provenance", {})

        results.append({
            "node_id": node.get("node_id"),
            "text": node.get("text", ""),
            "page_numbers": provenance.get("page_numbers", []),
            "score": score,
            "metadata": metadata
        })

    results.sort(
        key=lambda item: (-item["score"], item["node_id"] or "")
    )

    return results[:top_k]


if __name__ == "__main__":
    test_query = "ماذا يحدث للمادة الوراثية DNA قبل انقسام الخلية؟"

    print("Test query:", test_query)

    results = retrieve_chunks(test_query, top_k=3)

    for result in results:
        print(
            f"Chunk: {result['node_id']} | "
            f"Pages: {result['page_numbers']} | "
            f"Score: {result['score']}"
        )
        print(result["text"][:250])
        print("-" * 50)
