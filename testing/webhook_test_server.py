import http.server
import json
import logging

class WebhookHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body)
        except Exception:
            data = body.decode(errors='ignore')
        logging.info(f"Received webhook: {json.dumps(data, ensure_ascii=False, indent=2)}")
        with open("/tmp/webhook_test.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run(server_class=http.server.HTTPServer, handler_class=WebhookHandler, port=8088):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Webhook test server running on port {port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
