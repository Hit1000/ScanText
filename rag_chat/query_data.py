import argparse
# from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_openai import ChatOpenAI
import os
import re

from get_embedding_function import get_embedding_function

CHROMA_PATH = "chroma"


def main():
    # Create CLI.
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text.")
    args = parser.parse_args()
    query_text = args.query_text
    query_rag(query_text)


def query_rag(query_text: str):
    # Prepare the DB.
    embedding_function = get_embedding_function()
    db = Chroma(
        persist_directory=CHROMA_PATH, 
        embedding_function=embedding_function,
        collection_name="rag_tutorial"
    )

    try:
        # Search the DB directly
        results = db.similarity_search(query_text, k=5)
        
        if not results:
            response_text = "No relevant information found in the knowledge base."
        else:
            # Combine document contents
            context_text = "\n\n".join([doc.page_content for doc in results])
            # Get response
            response_text = simple_keyword_response(query_text, context_text)
        
        # Format source information
        sources = [doc.metadata.get("id", None) for doc in results] if results else []
        formatted_response = f"Response: {response_text}\nSources: {sources}"
        print(formatted_response)
        return response_text
    
    except Exception as e:
        error_message = f"Error querying the database: {str(e)}"
        print(error_message)
        return error_message


def simple_keyword_response(query: str, context: str) -> str:
    """Generate a simple response by matching keywords in the query to sentences in the context."""
    # Break context into sentences
    sentences = re.split(r'(?<=[.!?])\s+', context)
    
    # Break query into words (ignoring short words)
    query_words = set(word.lower() for word in query.split() if len(word) > 3)
    
    # Find sentences containing query words
    relevant_sentences = []
    for sentence in sentences:
        if any(word in sentence.lower() for word in query_words):
            relevant_sentences.append(sentence)
    
    if relevant_sentences:
        return "Based on the provided information: " + " ".join(relevant_sentences)
    else:
        return "I couldn't find a direct answer to your question in the available information."


if __name__ == "__main__":
    main()
