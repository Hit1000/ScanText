import os
import re
import glob
from PyPDF2 import PdfReader

def get_documents():
    txt_files = glob.glob("rag_chat/data/*.txt")
    pdf_files = glob.glob("rag_char/data/*.pdf")
    documents = []

    # Read .txt files
    for file_path in txt_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                documents.append({
                    "content": content,
                    "source": file_path
                })
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    # Read .pdf files
    for file_path in pdf_files:
        try:
            content = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                for page in pdf_reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        content += extracted + "\n"
            if content.strip():
                documents.append({
                    "content": content,
                    "source": file_path
                })
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return documents

def search_documents(query, documents):
    query_words = set(word.lower() for word in query.split() if len(word) > 3)
    if not query_words:
        query_words = set(word.lower() for word in query.split())

    results = []
    for doc in documents:
        content = doc["content"]
        score = sum(content.lower().count(word) for word in query_words)
        if score > 0:
            results.append({
                "content": content,
                "source": doc["source"],
                "score": score
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:1]

def generate_response(query, results):
    if not results:
        return "No relevant information found in the knowledge base."

    combined_content = "\n\n".join([r["content"] for r in results])
    sentences = re.split(r'(?<=[.!?])\s+', combined_content)

    query_words = set(word.lower() for word in query.split() if len(word) > 3)
    if not query_words:
        query_words = set(word.lower() for word in query.split())

    relevant_sentences = [s for s in sentences if any(w in s.lower() for w in query_words)]

    if relevant_sentences:
        response = "Based on the available information: " + " ".join(relevant_sentences)
    else:
        response = "Based on the available information: " + " ".join(sentences[:1])

    sources = [os.path.basename(r["source"]) for r in results]
    response += f"\n\nSources: {', '.join(sources)}"
    return response

def answer_query(query):
    documents = get_documents()
    results = search_documents(query, documents)
    response = generate_response(query, results)
    return response
