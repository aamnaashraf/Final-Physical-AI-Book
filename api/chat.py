from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime

# LangChain / AI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser

# Vector DB
from pinecone import Pinecone

# Global variables for caching
llm_model = None
pinecone_index = None
conversation_history = []

def initialize_models():
    """Initialize Groq and Pinecone"""
    global llm_model, pinecone_index

    if llm_model is not None and pinecone_index is not None:
        return

    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT")
    PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "rag-chatbot-768")

    if not GROQ_API_KEY or not PINECONE_API_KEY:
        raise ValueError("Missing required API keys")

    # Initialize Groq (fast and free!)
    llm_model = ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=GROQ_API_KEY,
        temperature=0.3
    )

    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
    pinecone_index = pc.Index(PINECONE_INDEX_NAME)

def simple_embed(text: str):
    """Simple text embedding using character-based hashing"""
    # This is a placeholder - we'll use Pinecone's query with text directly
    # For now, return a simple representation
    import hashlib
    hash_obj = hashlib.sha256(text.encode())
    hash_hex = hash_obj.hexdigest()
    # Convert to a simple vector (this is just for demonstration)
    return [float(int(hash_hex[i:i+2], 16)) / 255.0 for i in range(0, min(len(hash_hex), 1536), 2)]

def get_rag_response(query: str, software: str = None, hardware: str = None):
    """Generate RAG response using Groq"""
    global llm_model, pinecone_index, conversation_history

    # For now, skip vector search and just use the LLM
    # We'll add embeddings back once we solve the basic connectivity

    personalization_context = ""
    if software or hardware:
        personalization_context = f"User background: software={software}, hardware={hardware}\n"

    system_prompt = (
        "You are an expert AI assistant for Physical AI and Humanoid Robotics. "
        "Answer questions about ROS 2, NVIDIA Isaac Sim, Digital Twins, and VLA models. "
        f"{personalization_context}"
    )

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", "{input}")]
    )

    chain = prompt | llm_model | StrOutputParser()
    response = chain.invoke({"input": query})

    timestamp = datetime.now().isoformat()
    conversation_history.append({"role": "user", "content": query, "timestamp": timestamp})
    conversation_history.append({"role": "assistant", "content": response, "timestamp": timestamp})

    if len(conversation_history) > 7:
        conversation_history = conversation_history[-7:]

    return {
        "answer": response,
        "sources": [],
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
