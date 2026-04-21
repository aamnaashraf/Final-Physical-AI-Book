from http.server import BaseHTTPRequestHandler
import json
import os
from datetime import datetime

# Global variables
llm_model = None
conversation_history = []

def initialize_groq():
    """Initialize Groq LLM"""
    global llm_model

    if llm_model is not None:
        return

    try:
        from langchain_groq import ChatGroq

        GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
        if not GROQ_API_KEY:
            raise ValueError("Missing GROQ_API_KEY")

        llm_model = ChatGroq(
            model="llama-3.3-70b-versatile",
            groq_api_key=GROQ_API_KEY,
            temperature=0.3,
            max_tokens=1024,
            timeout=8  # 8 seconds to stay under Vercel's 10s limit
        )
    except Exception as e:
        raise Exception(f"Groq initialization failed: {str(e)}")

def get_ai_response(query: str, software: str = None, hardware: str = None):
    """Generate AI response using Groq"""
    global llm_model, conversation_history

    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser

        personalization = ""
        if software or hardware:
            personalization = f"\n\nUser context: Using {software or 'unspecified software'} and {hardware or 'unspecified hardware'}."

        system_prompt = (
            "You are an expert AI assistant for Physical AI and Humanoid Robotics. "
            "You help students learn about ROS 2, NVIDIA Isaac Sim, Digital Twins, VLA models, and humanoid robotics. "
            "Provide clear, concise answers."
            f"{personalization}"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}")
        ])

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
    except Exception as e:
        raise Exception(f"AI response generation failed: {str(e)}")

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            # Read request
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))

            query = data.get("query", "")
            if not query:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Query is required"}).encode())
                return

            # Initialize and get response
            initialize_groq()
            result = get_ai_response(query, data.get("software"), data.get("hardware"))

            # Send success response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            error_msg = str(e)
            print(f"Error: {error_msg}")

            import traceback
            traceback.print_exc()

            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            error_response = {
                "answer": f"Error: {error_msg}",
                "error": error_msg,
                "sources": [],
                "conversation_history": []
            }
            self.wfile.write(json.dumps(error_response).encode())
