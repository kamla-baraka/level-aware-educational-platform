
"""
Compare generation context coverage for Top-K=3 and 5.
Does not permanently modify generation settings.
"""

import re
import generation
from retrieval import load_knowledge_base
from test_context_coverage import REQUIRED_CHUNKS


def evaluate(top_k, chunks):
    generation.RETRIEVAL_TOP_K = top_k

    total_found = 0
    total_required = 0

    print(f"\n=== TOP-K = {top_k} ===")

    for part in generation.PARTS:
        context = generation.get_context(part, chunks)

        retrieved = set(
            re.findall(r"(?m)^\[(C\d+)\]$", context)
        )

        required = set(REQUIRED_CHUNKS[part["title"]])
        missing = required - retrieved

        found = len(required & retrieved)
        coverage = found / len(required)

        total_found += found
        total_required += len(required)

        print(f"\nPart: {part['title']}")
        print(f"Retrieved: {sorted(retrieved)}")
        print(f"Missing: {sorted(missing)}")
        print(f"Coverage: {coverage:.2%}")
        print(f"Context chunks: {len(retrieved)}")

    overall = total_found / total_required

    print(f"\nOverall coverage: {overall:.2%}")

    return overall


def main():
    chunks = load_knowledge_base()
    original_top_k = generation.RETRIEVAL_TOP_K

    try:
        results = {}

        for top_k in [3, 5]:
            results[top_k] = evaluate(top_k, chunks)

        print("\n=== TOP-K COMPARISON ===")
        for top_k, coverage in results.items():
            print(f"Top-K={top_k}: {coverage:.2%}")

    finally:
        generation.RETRIEVAL_TOP_K = original_top_k


if __name__ == "__main__":
    main()
