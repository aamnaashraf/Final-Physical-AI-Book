from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            # Step 1: Test basic functionality
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            query = data.get("query", "")

            # Step 2: Try importing Groq
            try:
                from langchain_groq import ChatGroq
                import_status = "Groq imported successfully"
            except Exception as e:
                import_status = f"Groq import failed: {str(e)}"

            # Step 3: Check environment variables
            groq_key = os.environ.get("GROQ_API_KEY")
            env_status = "Groq key found" if groq_key else "Groq key missing"

            response = {
                "answer": f"Debug info - Query: '{query}', Import: {import_status}, Env: {env_status}",
                "sources": [],
                "conversation_history": []
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {"answer": f"Error: {str(e)}", "error": str(e)}
            self.wfile.write(json.dumps(error_response).encode())
