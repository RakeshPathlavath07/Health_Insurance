"""
PDF Ingestion & FAISS Vector Indexing Pipeline
Downloads policy brochure/wording PDFs, extracts text from top relevant pages,
chunks document content, and indexes into persistent FAISS vector store.
"""
import os
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import requests
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

FAISS_INDEX_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../faiss_index")
)

def get_embeddings():
    """Initializes local HuggingFace embeddings model lazily."""
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )

def extract_text_from_pdf(pdf_path_or_url: str, max_pages: int = 15) -> str:
    """Extracts raw text from top 15 pages of PDF using pdfplumber."""
    temp_pdf = None
    try:
        if pdf_path_or_url.startswith("http://") or pdf_path_or_url.startswith("https://"):
            response = requests.get(pdf_path_or_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            if response.status_code != 200:
                print(f"Failed to download PDF: HTTP {response.status_code}")
                return ""
            temp_pdf = os.path.join(os.path.dirname(__file__), "temp_policy.pdf")
            with open(temp_pdf, "wb") as f:
                f.write(response.content)
            target_path = temp_pdf
        else:
            target_path = pdf_path_or_url

        extracted_pages = []
        with pdfplumber.open(target_path) as pdf:
            pages_to_read = pdf.pages[:max_pages]
            for page_idx, page in enumerate(pages_to_read):
                text = page.extract_text()
                if text and len(text.strip()) > 50:
                    extracted_pages.append(f"--- Page {page_idx+1} ---\n" + text.strip())

        return "\n\n".join(extracted_pages)
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""
    finally:
        if temp_pdf and os.path.exists(temp_pdf):
            try:
                os.remove(temp_pdf)
            except Exception:
                pass

def ingest_pdf(pdf_path_or_url: str, provider: str, policy_name: str) -> bool:
    """
    Ingests PDF document into persistent FAISS vector store.
    Loads existing FAISS index if present and appends new chunks (does not overwrite).
    """
    from langchain_community.vectorstores import FAISS
    raw_text = extract_text_from_pdf(pdf_path_or_url)
    if not raw_text:
        print("No text extracted from PDF, aborting vector ingestion.")
        return False

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
    text_chunks = splitter.split_text(raw_text)

    docs = [
        Document(
            page_content=chunk,
            metadata={
                "provider": provider.lower(),
                "policy_name": policy_name.lower(),
                "source": pdf_path_or_url
            }
        )
        for chunk in text_chunks
    ]

    embeddings = get_embeddings()

    os.makedirs(FAISS_INDEX_DIR, exist_ok=True)
    index_file = os.path.join(FAISS_INDEX_DIR, "index.faiss")

    if os.path.exists(index_file):
        print("Loading existing FAISS index to append new documents...")
        vector_db = FAISS.load_local(FAISS_INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
        vector_db.add_documents(docs)
    else:
        print("Creating fresh FAISS vector index...")
        vector_db = FAISS.from_documents(docs, embeddings)

    vector_db.save_local(FAISS_INDEX_DIR)
    print(f"Successfully ingested {len(docs)} text chunks for '{policy_name}' into FAISS index!")
    return True

if __name__ == "__main__":
    test_url = "https://www.icicilombard.com/docs/default-source/assets/health-advait-policy-clause.pdf"
    ingest_pdf(test_url, provider="icici-lombard", policy_name="icici-lombard-health-advait")
