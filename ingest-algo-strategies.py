from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import TokenTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

splitter = TokenTextSplitter(chunk_size=250, chunk_overlap=50)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = Chroma(collection_name="algo-strategies", embedding_function=embeddings, persist_directory="./chroma_db")
docs = PyPDFDirectoryLoader(path="./docs/", glob="*.pdf").load()
chunks = splitter.split_documents(docs)
vector_store.add_documents(chunks)