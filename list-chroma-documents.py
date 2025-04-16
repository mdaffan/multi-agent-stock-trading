from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import uuid
import sys

def main():
    # Initialize the same embeddings model as in the ingestion script
    print("Initializing embeddings model...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # Access the existing Chroma vector store with the same persistence directory
    print("Connecting to Chroma vector store...")
    vector_store = Chroma(collection_name="algo-strategies", embedding_function=embeddings, persist_directory="./chroma_db")

    # Get all documents from the vector store
    print("\nRetrieving documents from the vector store...\n")
    collection = vector_store._collection
    
    # Get document count
    doc_count = collection.count()
    print(f"Total documents in vector store: {doc_count}\n")

    # Display documents and their metadata
    if doc_count > 0:
        # Get all documents
        results = collection.get()
        
        # Extract document IDs, metadatas, and contents
        doc_ids = results.get('ids', [])
        metadatas = results.get('metadatas', [])
        documents = results.get('documents', [])
        
        # Display information
        print(f"{'ID':<40} | {'Source':<30} | {'Page':<6} | {'Content Preview':<50}")
        print("-" * 130)
        
        for i in range(min(len(doc_ids), 10)):  # Show first 10 docs to avoid overwhelming output
            metadata = metadatas[i] if i < len(metadatas) else {}
            doc = documents[i] if i < len(documents) else ""
            source = metadata.get('source', 'Unknown')
            page = metadata.get('page', 'N/A')
            
            # Truncate document content for display
            preview = doc[:50] + "..." if len(doc) > 50 else doc
            
            print(f"{doc_ids[i]:<40} | {source:<30} | {page:<6} | {preview:<50}")
        
        if len(doc_ids) > 10:
            print(f"\n... and {len(doc_ids) - 10} more documents")
        
        # Provide guidance for searching
        print("\nTo search the vector store, you can use:")
        print("vector_store.similarity_search('your query here', k=3)")
    else:
        print("No documents found in the vector store.")

if __name__ == "__main__":
    main()

