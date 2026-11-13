
"""
Compare original and refined RAG queries.

Keeps the production generation.py unchanged.
Evaluates curriculum coverage and context size.
"""

import re

import generation
from retrieval import load_knowledge_base
from test_context_coverage import REQUIRED_CHUNKS


REFINED_QUERIES = {
    "المفاهيم والأمثلة": [
        "مقارنة الانقسام المتساوي والمنصف",
        "الكروموسوم المتضاعف والكروماتيدات الشقيقة والسنترومير",
    ],
    "التمارين والتقييم": [
        "مراحل الانقسام المتساوي والانقسام المنصف",
        "انقسام السيتوبلازم في الخلية النباتية والحيوانية",
    ],
}


def evaluate(label, chunks, refined=False):
    total_found = 0
    total_required = 0
    total_context_chunks = 0

    print(f"\n=== {label} ===")

    for part in generation.PARTS:
        test_part = dict(part)

        if refined and part["title"] in REFINED_QUERIES:
            test_part["queries"] = REFINED_QUERIES[part["title"]]

        context = generation.get_context(test_part, chunks)

        retrieved = set(
            re.findall(r"(?m)^\[(C\d+)\]$", context)
        )

        required = set(REQUIRED_CHUNKS[part["title"]])
        missing = required - retrieved

        found = len(required & retrieved)

        total_found += found
        total_required += len(required)
        total_context_chunks += len(retrieved)

        print(f"\nPart: {part['title']}")
        print(f"Retrieved: {sorted(retrieved)}")
        print(f"Missing: {sorted(missing)}")
        print(f"Coverage: {found / len(required):.2%}")
        print(f"Context chunks: {len(retrieved)}")

    overall = total_found / total_required

    print(f"\nOverall coverage: {overall:.2%}")
    print(f"Total context chunks: {total_context_chunks}")

    return overall, total_context_chunks


def main():
    chunks = load_knowledge_base()
    original_top_k = generation.RETRIEVAL_TOP_K

    try:
        generation.RETRIEVAL_TOP_K = 3

        original = evaluate(
            "ORIGINAL QUERIES",
            chunks,
            refined=False,
        )

        refined = evaluate(
            "REFINED QUERIES",
            chunks,
            refined=True,
        )

        print("\n=== QUERY REFINEMENT COMPARISON ===")
        print(
            f"Original coverage: {original[0]:.2%} "
            f"| Context chunks: {original[1]}"
        )
        print(
            f"Refined coverage: {refined[0]:.2%} "
            f"| Context chunks: {refined[1]}"
        )

    finally:
        generation.RETRIEVAL_TOP_K = original_top_k


if __name__ == "__main__":
    main()
