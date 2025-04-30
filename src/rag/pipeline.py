# pipeline.py
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_community.cache import SQLiteCache
import langchain_core
import time
import os

# Enable caching
langchain_core.llm_cache = SQLiteCache(database_path=".langchain.db")

def create_rag_chain(vectorstore):
    """
    Create a Retrieval-Augmented Generation chain using the provided vector store
    
    Args:
        vectorstore: Vector store for document retrieval
        
    Returns:
        RetrievalQA chain
    """
    # Initialize LLM
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0
    )

    # Custom prompt template
    template = """You are a legal assistant helping lawyers find relevant information.
    Use the following pieces of context to answer the question at the end.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.

    {context}

    Question: {question}
    Answer: """

    PROMPT = PromptTemplate(
        template=template,
        input_variables=["context", "question"]
    )

    # Create RAG pipeline
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
        chain_type_kwargs={"prompt": PROMPT},
        return_source_documents=True
    )
    
    return qa
