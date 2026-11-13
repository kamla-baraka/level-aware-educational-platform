
from generation import PARTS, get_context
from retrieval import load_knowledge_base


def test_rag_context():
    all_chunks = load_knowledge_base()

    print("\n=== RAG RETRIEVAL TEST ===")

    for part in PARTS:
        context = get_context(part, all_chunks)

        retrieved_ids = [
            chunk["node_id"]
            for chunk in all_chunks
            if f"[{chunk['node_id']}]" in context
        ]

        print(f"\nPart: {part['title']}")
        print(f"Queries: {part['queries']}")
        print(f"Retrieved IDs: {retrieved_ids}")
        print(f"Number of chunks: {len(retrieved_ids)}")

        assert context.strip(), (
            f"Empty context for {part['title']}"
        )

        assert retrieved_ids, (
            f"No chunks retrieved for {part['title']}"
        )

    print("\nAll RAG context tests passed!")


if __name__ == "__main__":
    test_rag_context()
