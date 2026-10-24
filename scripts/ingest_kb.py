"""Build the vector store.

Indexes (1) the hand-written policy files and (2) rows from the Bitext
customer-support dataset. 50 Bitext rows are held out and saved to
tests/bitext_holdout.json so evaluation never sees indexed data.

Run:  python scripts/ingest_kb.py                 # policies + 3000 Bitext rows
      python scripts/ingest_kb.py --policy-only   # offline / quick start
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.documents import Document  # noqa: E402
from langchain_text_splitters import RecursiveCharacterTextSplitter  # noqa: E402

from app import config  # noqa: E402

BITEXT = "bitext/Bitext-customer-support-llm-chatbot-training-dataset"
POLICY_CATEGORY = {  # which ticket category a policy file mainly belongs to
    "refund_policy": "REFUND", "cancellation_policy": "CANCEL",
    "shipping_and_delivery": "DELIVERY", "payment_and_billing": "PAYMENT",
    "account_and_contact": "ACCOUNT", "escalation_policy": "GENERAL",
}


def load_policies() -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    docs = []
    for path in sorted(config.KB_DOCS_DIR.glob("*.md")):
        meta = {"source": path.name, "type": "policy",
                "category": POLICY_CATEGORY.get(path.stem, "GENERAL")}
        docs += splitter.create_documents([path.read_text(encoding="utf-8")], metadatas=[meta])
    return docs


def load_bitext(rows: int, holdout: int) -> list[Document]:
    from datasets import load_dataset

    ds = load_dataset(BITEXT, split="train").shuffle(seed=42)
    held = [{"ticket": r["instruction"], "category": r["category"], "intent": r["intent"]}
            for r in ds.select(range(holdout))]
    (config.TESTS_DIR / "bitext_holdout.json").write_text(json.dumps(held, indent=2))
    print(f"Saved {len(held)} held-out tickets to tests/bitext_holdout.json")

    return [
        Document(
            page_content=f"Q: {r['instruction']}\nA: {r['response']}",
            metadata={"source": "bitext", "type": "faq",
                      "category": r["category"], "intent": r["intent"]},
        )
        for r in ds.select(range(holdout, holdout + rows))
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=3000)
    parser.add_argument("--holdout", type=int, default=50)
    parser.add_argument("--policy-only", action="store_true")
    args = parser.parse_args()

    docs = load_policies()
    print(f"Policy chunks: {len(docs)}")
    if not args.policy_only:
        try:
            faq = load_bitext(args.rows, args.holdout)
            docs += faq
            print(f"Bitext FAQ rows: {len(faq)}")
        except Exception as exc:  # no internet / dataset moved
            print(f"WARNING: could not load Bitext ({exc}). Indexing policies only.")

    from langchain_chroma import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings

    if config.VECTORSTORE_DIR.exists():
        shutil.rmtree(config.VECTORSTORE_DIR)
    config.VECTORSTORE_DIR.mkdir(parents=True)

    store = Chroma(
        collection_name=config.COLLECTION_NAME,
        embedding_function=HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL),
        persist_directory=str(config.VECTORSTORE_DIR),
    )
    for i in range(0, len(docs), 500):
        store.add_documents(docs[i:i + 500])
        print(f"Indexed {min(i + 500, len(docs))}/{len(docs)}")
    print("Done.")


if __name__ == "__main__":
    main()
