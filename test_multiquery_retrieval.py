
"""
Preliminary Multi-Query Retrieval Experiment.

Compare original two-query retrieval with
multiple concept-focused queries at Top-K=3.

Does not modify the production generation.py.
"""

import re

import generation
from retrieval import load_knowledge_base
from test_context_coverage import REQUIRED_CHUNKS


MULTI_QUERIES = {
    "الأهداف والكروموسومات": [
        "عدد الكروموسومات في الكائنات الحية",
        "تضاعف المادة الوراثية DNA قبل انقسام الخلية",
        "تركيب الكروموسوم المتضاعف والكروماتيدات",
        "الطور البيني وأهمية الانقسام المتساوي",
    ],
    "الانقسام المتساوي": [
        "الخلايا الجسمية والانقسام المتساوي",
        "الطور البيني وأهمية الانقسام المتساوي",
        "مراحل الانقسام المتساوي الأربع",
        "انقسام السيتوبلازم في الخلية النباتية والحيوانية",
    ],
    "الانقسام المنصف ومتلازمة داون": [
        "الانقسام المنصف والخلايا التناسلية",
        "عدد الخلايا والكروموسومات الناتجة عن الانقسام المنصف",
        "القصة الواردة في المنهاج عن متلازمة داون",
        "متلازمة داون والكروموسوم 21",
    ],
    "المفاهيم والأمثلة": [
        "تضاعف DNA قبل انقسام الخلية",
        "الكروموسوم المتضاعف والكروماتيدات والسنترومير",
        "الخلايا الجسمية والانقسام المتساوي",
        "مراحل الانقسام المتساوي",
        "الانقسام المنصف والخلايا التناسلية",
    ],
    "التمارين والتقييم": [
        "الخلايا الجسمية والانقسام المتساوي",
        "مراحل الانقسام المتساوي",
        "انقسام السيتوبلازم في الخلية النباتية والحيوانية",
        "الانقسام المنصف وعدد الكروموسومات",
        "متلازمة داون والكروموسوم 21",
    ],
}


def evaluate(label, chunks, use_multi=False):
    total_found = 0
    total_required = 0
    total_context_chunks = 0

    print(f"\n=== {label} ===")

    for part in generation.PARTS:
        test_part = dict(part)

        if use_multi:
            test_part["queries"] = MULTI_QUERIES[part["title"]]

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
            "ORIGINAL TWO-QUERY RETRIEVAL",
            chunks,
            use_multi=False,
        )

        multi = evaluate(
            "MULTI-QUERY RETRIEVAL",
            chunks,
            use_multi=True,
        )

        print("\n=== MULTI-QUERY COMPARISON ===")
        print(
            f"Original coverage: {original[0]:.2%} "
            f"| Context chunks: {original[1]}"
        )
        print(
            f"Multi-query coverage: {multi[0]:.2%} "
            f"| Context chunks: {multi[1]}"
        )

    finally:
        generation.RETRIEVAL_TOP_K = original_top_k


if __name__ == "__main__":
    main()
