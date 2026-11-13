
"""
Preliminary curriculum context coverage test.

Checks whether the RAG-selected context contains
the curriculum chunks needed for each learning part.

Coverage labels are provisional and require review.
"""

from generation import PARTS, get_context
from retrieval import load_knowledge_base


# Preliminary curriculum coverage requirements.
REQUIRED_CHUNKS = {
    "الأهداف والكروموسومات": [
        "C01", "C02", "C03", "C05"
    ],
    "الانقسام المتساوي": [
        "C04", "C05", "C06", "C08"
    ],
    "الانقسام المنصف ومتلازمة داون": [
        "C09", "C10", "C11"
    ],
    "المفاهيم والأمثلة": [
        "C02", "C03", "C04", "C06", "C09"
    ],
    "التمارين والتقييم": [
        "C04", "C06", "C08", "C09", "C11"
    ],
}


def main():
    chunks = load_knowledge_base()

    print("\n=== GENERATION CONTEXT COVERAGE ===")

    total_required = 0
    total_found = 0

    for part in PARTS:
        title = part["title"]
        context = get_context(part, chunks)

        retrieved_ids = {
            chunk["node_id"]
            for chunk in chunks
            if f"[{chunk['node_id']}]" in context
        }

        required = set(REQUIRED_CHUNKS[title])

        found = required & retrieved_ids
        missing = required - retrieved_ids

        coverage = len(found) / len(required)

        total_required += len(required)
        total_found += len(found)

        print(f"\nPart: {title}")
        print(f"Retrieved: {sorted(retrieved_ids)}")
        print(f"Required: {sorted(required)}")
        print(f"Missing: {sorted(missing)}")
        print(f"Coverage: {coverage:.2%}")

    overall = total_found / total_required

    print("\n=== COVERAGE SUMMARY ===")
    print(f"Overall coverage: {overall:.2%}")
    print(f"Required chunk occurrences: {total_required}")
    print(f"Covered chunk occurrences: {total_found}")

    print("\nCoverage evaluation completed.")


if __name__ == "__main__":
    main()
