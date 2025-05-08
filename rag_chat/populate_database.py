import argparse
import os
import shutil
from langchain_community.document_loaders import TextLoader, DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from get_embedding_function import get_embedding_function
from langchain_chroma import Chroma


CHROMA_PATH = "chroma"
DATA_PATH = "data"


def main():
    # Check if the database should be cleared (using the --clear flag).
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Reset the database.")
    args = parser.parse_args()
    if args.reset:
        print("✨ Clearing Database")
        clear_database()

    # Create (or update) the data store.
    documents = load_documents()
    chunks = split_documents(documents)
    add_to_chroma(chunks)


def load_documents():
    documents = []
    
    # Load text files
    text_loader = DirectoryLoader(
        DATA_PATH, 
        glob="**/*.txt",
        loader_cls=TextLoader
    )
    documents.extend(text_loader.load())
    
    # Load PDF files
    # pdf_loader = DirectoryLoader(
    #     DATA_PATH,
    #     glob="**/*.pdf",
    #     loader_cls=PyPDFLoader
    # )
    # documents.extend(pdf_loader.load())
    
    print(f"Loaded {len(documents)} documents from {DATA_PATH}")
    return documents


def split_documents(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)


def add_to_chroma(chunks: list[Document]):
    # Load the existing database.
    embedding_function = get_embedding_function()
    
    # Create a new Chroma client
    db = Chroma(
        persist_directory=CHROMA_PATH, 
        embedding_function=embedding_function,
        collection_name="rag_tutorial"
    )

    # Calculate Page IDs.
    chunks_with_ids = calculate_chunk_ids(chunks)

    # Only add documents that don't exist in the DB.
    if not chunks_with_ids:
        print("No documents to add")
        return
        
    try:
        # Get existing documents to check for duplicates
        existing_items = db.get()
        existing_ids = set(existing_items["ids"]) if existing_items["ids"] else set()
        print(f"Number of existing documents in DB: {len(existing_ids)}")

        # Filter out documents that already exist
        new_chunks = []
        for chunk in chunks_with_ids:
            if chunk.metadata["id"] not in existing_ids:
                new_chunks.append(chunk)
    except Exception as e:
        print(f"Error getting existing documents: {e}")
        # If there's an error, assume all documents are new
        new_chunks = chunks_with_ids
        print("Assuming all documents are new")

    if len(new_chunks):
        print(f"👉 Adding new documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        db.add_documents(new_chunks, ids=new_chunk_ids)
    else:
        print("✅ No new documents to add")


def calculate_chunk_ids(chunks):
    # This will create IDs like "data/monopoly.txt:1:2" or "data/document.pdf:1:2"
    # Source file : Page Number : Chunk Index

    last_source = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source", "unknown")
        # Use page number if available (PDFs have this), otherwise use line_number or default to 1
        page = chunk.metadata.get("page", chunk.metadata.get("line_number", 1))
        current_source_page = f"{source}:{page}"

        # If the source+page is the same as the last one, increment the index
        if current_source_page == last_source:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        # Calculate the chunk ID
        chunk_id = f"{current_source_page}:{current_chunk_index}"
        last_source = current_source_page

        # Add it to the chunk metadata
        chunk.metadata["id"] = chunk_id

    return chunks


def clear_database():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)


if __name__ == "__main__":
    main()