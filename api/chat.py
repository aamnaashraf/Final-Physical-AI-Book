from http.server import BaseHTTPRequestHandler
import json
import os
from typing import List, Dict
from datetime import datetime

# LangChain / AI
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser

# Vector DB
from pinecone import Pinecone

# Global variables for caching
embeddings_model = None
llm_model = None
pinecone_index = None
conversation_history = []

def initialize_models():
    """Initialize AI models and Pinecone connection"""
    global embeddings_model, llm_model, pinecone_index

    if embeddings_model is not None and llm_model is not None and pinecone_index is not None:
        return

    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT")
    PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "rag-chatbot-768")

    if not GOOGLE_API_KEY or not PINECONE_API_KEY:
        raise ValueError("Missing required API keys")

    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=GOOGLE_API_KEY
    )

    llm_model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.3
    )

    pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
    pinecone_index = pc.Index(PINECONE_INDEX_NAME)

def get_rag_response(query: str, software: str = None, hardware: str = None):
    """Generate RAG response"""
    global embeddings_model, llm_model, pinecone_index, conversation_history

    query_vector = embeddings_model.embed_query(query)
    results = pinecone_index.query(vector=query_vector, top_k=5, include_metadata=True)

    retrieved_docs = []
    sources_list = []

    for match in results.matches:
        content = match.metadata.get("text", "")
        source_path = match.metadata.get("source", "N/A")
        filename = match.metadata.get("filename", "N/A")
        doc_url = f"/docs/{source_path.replace('.md', '').replace('.mdx', '')}"

        retrieved_docs.append(Document(
            page_content=content,
            metadata={"source": doc_url, "score": match.score, "filename": filename}
        ))

        if {"source": doc_url, "filename": filename} not in sources_list:
            sources_list.append({"source": doc_url, "filename": filename})

    conversation_context = "\n".join([f"{m['role']}: {m['content']}" for m in conversation_history[-6:]])

    personalization_context = ""
    if software or hardware:
        personalization_context = f"User background: software={software}, hardware={hardware}\n"

    if not retrieved_docs:
        system_prompt = (
            "You are an expert AI assistant. Answer thoughtfully based on general AI and robotics knowledge."
            f"{personalization_context}"
        )
        context_str = ""
    else:
        system_prompt = (
            "You are an expert technical documentation assistant. Answer based exclusively on the provided docs."
            f"{personalization_context}"
        )
        context_str = "\n\n".join([f"[Source: {d.metadata['source']}]\n{d.page_content}" for d in retrieved_docs])

    full_context = conversation_context + "\n" + context_str

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt + "\n\nContext:\n{context}"), ("human", "{input}")]
    )

    def format_context(x):
        return {"input": x["input"], "context": full_context}

    chain = RunnableLambda(format_context) | prompt | llm_model | StrOutputParser()
    response = chain.invoke({"input": query})

    timestamp = datetime.now().isoformat()
    conversation_history.append({"role": "user", "content": query, "timestamp": timestamp})
    conversation_history.append({"role": "assistant", "content": response, "timestamp": timestamp})

    if len(conversation_history) > 7:
        conversation_history = conversation_history[-7:]

    return {
        "answer": response,
        "sources": sources_list,
        "conversation_history": conversation_history
    }

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            # Initialize models
            initialize_models()

            # Read request body
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))

            query = data.get("query", "")
            software = data.get("software")
            hardware = data.get("hardware")

            if not query:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Query is required"}).encode())
                return

            # Get RAG response
            result = get_rag_response(query, software, hardware)

            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()

            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {"answer": "Sorry, AI is unavailable right now.", "error": str(e)}
            self.wfile.write(json.dumps(error_response).encode())
