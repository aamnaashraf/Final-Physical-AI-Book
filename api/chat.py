from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime

# LangChain / AI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Global variables for caching
llm_model = None
conversation_history = []

def initialize_groq():
    """Initialize Groq LLM"""
    global llm_model

    if llm_model is not None:
        return

    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

    if not GROQ_API_KEY:
        raise ValueError("Missing GROQ_API_KEY")

    # Initialize Groq with fast Llama model
    llm_model = ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=GROQ_API_KEY,
        temperature=0.3,
        max_tokens=1024
    )

def get_ai_response(query: str, software: str = None, hardware: str = None):
    """Generate AI response using Groq"""
    global llm_model, conversation_history

    personalization = ""
    if software or hardware:
        personalization = f"\n\nUser context: Using {software or 'unspecified software'} and {hardware or 'unspecified hardware'}."

    system_prompt = (
        "You are an expert AI assistant for Physical AI and Humanoid Robotics. "
        "You help students and practitioners learn about:\n"
        "- ROS 2 (Robot Operating System)\n"
        "- NVIDIA Isaac Sim\n"
        "- Digital Twins (Gazebo, Unity)\n"
        "- Vision-Language-Action (VLA) models\n"
        "- Humanoid robotics and embodied AI\n\n"
        "Provide clear, practical answers with examples when helpful."
        f"{personalization}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])

    chain = prompt | llm_model | StrOutputParser()
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
            # Initialize Groq
            initialize_groq()

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

            # Get AI response
            result = get_ai_response(query, software, hardware)

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
