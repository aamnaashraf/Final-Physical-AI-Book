import os
import json
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

# Global variables for caching (to avoid re-initialization on every request)
embeddings_model = None
llm_model = None
pinecone_index = None
conversation_history = []

def initialize_models():
    """Initialize AI models and Pinecone connection (cached globally)"""
    global embeddings_model, llm_model, pinecone_index

    if embeddings_model is not None and llm_model is not None and pinecone_index is not None:
        return  # Already initialized

    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT")
    PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "rag-chatbot-768")

    if not GOOGLE_API_KEY or not PINECONE_API_KEY:
        raise ValueError("Missing required API keys")

    print("Initializing models...")

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

    print("Models initialized successfully")

async def get_rag_response(query: str, software: str = None, hardware: str = None):
    """Generate RAG response for the query"""
    global embeddings_model, llm_model, pinecone_index, conversation_history

    # Embed query
    query_vector = embeddings_model.embed_query(query)

    # Search Pinecone
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

    # Build conversation context
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

    # Update conversation history
    timestamp = datetime.now().isoformat()
    conversation_history.append({"role": "user", "content": query, "timestamp": timestamp})
    conversation_history.append({"role": "assistant", "content": response, "timestamp": timestamp})

    # Keep only last 7 messages
    if len(conversation_history) > 7:
        conversation_history = conversation_history[-7:]

    return {
        "answer": response,
        "sources": sources_list,
        "conversation_history": conversation_history
    }

def handler(request):
    """Vercel serverless function handler"""
    from http.server import BaseHTTPRequestHandler
    import asyncio

    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
            'body': ''
        }

    if request.method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json'},
            'body': json.dumps({"error": "Method not allowed"})
        }

    try:
        # Initialize models (cached after first call)
        initialize_models()

        # Parse request body
        body = request.json if hasattr(request, 'json') else json.loads(request.body)
        query = body.get("query", "")
        software = body.get("software")
        hardware = body.get("hardware")

        if not query:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json'},
                'body': json.dumps({"error": "Query is required"})
            }

        # Get RAG response
        result = asyncio.run(get_rag_response(query, software, hardware))

        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json'},
            'body': json.dumps(result)
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json'},
            'body': json.dumps({"answer": "Sorry, AI is unavailable right now.", "error": str(e)})
        }
