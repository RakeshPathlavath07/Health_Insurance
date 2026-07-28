"""
Test script for Item 4: Verifies metadata filtering & chunk isolation in rag_tool.py
"""
import sys
import json
from backend.app.tools.rag_tool import run_rag_tool, query_faiss_index, extract_query_brand

def test_chunk_isolation():
    print("=== ITEM 4: RAG TOOL CHUNK ISOLATION TEST ===")
    
    query = "What is the pre-existing disease waiting period in Niva Bupa ReAssure policy?"
    target_brand = extract_query_brand(query)
    
    print(f"User Query: '{query}'")
    print(f"Extracted Brand Keyword: '{target_brand}'")
    
    # Execute FAISS vector search directly to inspect retrieved chunks & metadata
    retrieved_docs = query_faiss_index(query, top_k=4, target_brand=target_brand)
    
    print("\n--- ACTUAL RETRIEVED CHUNKS ---")
    if not retrieved_docs:
        print("No local chunks retrieved. (Vector index empty or needs fallback).")
    else:
        for idx, doc in enumerate(retrieved_docs, 1):
            meta = doc.metadata
            print(f"\nChunk #{idx}:")
            print(f"  - Metadata Provider: {meta.get('provider', 'N/A')}")
            print(f"  - Metadata Policy Name: {meta.get('policy_name', 'N/A')}")
            print(f"  - Page Content Snippet: {doc.page_content[:200]}...")
            
    # Execute full RAG pipeline
    print("\n--- FINAL SYNTHESIZED ANSWER ---")
    answer, fallback_used = run_rag_tool(query)
    print(f"Fallback Triggered: {fallback_used}")
    print(f"Answer:\n{answer}")

if __name__ == "__main__":
    test_chunk_isolation()
