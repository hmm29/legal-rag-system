# rag_system.py
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.cache import SQLiteCache
import langchain
import time

# Enable caching
langchain.llm_cache = SQLiteCache(database_path=".langchain.db")

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

