from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error

conversation_history = []

def call_groq_api(query: str, software: str = None, hardware: str = None):
    """Call Groq API directly using urllib"""

    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    if not GROQ_API_KEY:
        raise ValueError("Missing GROQ_API_KEY")

    personalization = ""
    if software or hardware:
        personalization = f"\n\nUser context: Using {software or 'unspecified'} and {hardware or 'unspecified'}."

    system_prompt = (
        "You are an expert AI assistant for Physical AI and Humanoid Robotics. "
        "You help students learn about ROS 2, NVIDIA Isaac Sim, Digital Twins, VLA models, and humanoid robotics. "
        "Provide clear, concise answers."
        f"{personalization}"
    )

    # Prepare request to Groq API
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        "temperature": 0.3,
        "max_tokens": 1024
    }

    # Make request
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            result = json.loads(response.read().decode('utf-8'))
            answer = result['choices'][0]['message']['content']

            # Update conversation history
            from datetime import datetime
            timestamp = datetime.now().isoformat()
            conversation_history.append({"role": "user", "content": query, "timestamp": timestamp})
            conversation_history.append({"role": "assistant", "content": answer, "timestamp": timestamp})

            if len(conversation_history) > 7:
                conversation_history[:] = conversation_history[-7:]

            return {
                "answer": answer,
                "sources": [],
                "conversation_history": conversation_history
            }
    except urllib.error.URLError as e:
        raise Exception(f"Network error: {str(e)}")
    except Exception as e:
        raise Exception(f"API call failed: {str(e)}")

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
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

            result = call_groq_api(query, data.get("software"), data.get("hardware"))

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            print(f"Error: {str(e)}")

            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            error_response = {
                "answer": f"AI Error: {str(e)}. Please try again.",
                "error": str(e),
                "sources": [],
                "conversation_history": []
            }
            self.wfile.write(json.dumps(error_response).encode())
