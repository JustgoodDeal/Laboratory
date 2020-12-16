from api import add_line, change_line, del_line, get_line, get_posts
from http.server import BaseHTTPRequestHandler, HTTPServer
from utils import parse_url


class Server(BaseHTTPRequestHandler):
    def respond_to_request(self, status_code, content_type, content):
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.end_headers()
        self.wfile.write(bytes(content, "utf-8"))

    def do_GET(self):
        url = self.path[1:]
        if url:
            response = {}
            number = parse_url(url)
            if not number:
                status_code = 404
            elif type(number) == str:
                response = get_posts()
                status_code = response['status_code']
            else:
                response = get_line(number)
                status_code = response['status_code']
            content_type = "application/json"
            content = response.get('content', '')
        else:
            content_type = "text/html"
            content = "<h1>Server</h1>"
            status_code = 200
        self.respond_to_request(status_code, content_type, content)

    def do_POST(self):
        url = self.path
        content_type = "application/json"
        if url == "/posts/":
            content_length = int(self.headers['Content-Length'])
            post_body = self.rfile.read(content_length)
            response = add_line(post_body)
            content = response.get('content', '')
            status_code = response['status_code']
        else:
            content = ''
            status_code = 404
        self.respond_to_request(status_code, content_type, content)

    def do_DELETE(self):
        url = self.path[1:]
        content_type = "application/json"
        content = ''
        status_code = 404
        if url:
            number = parse_url(url)
            if number and type(number) == int:
                response = del_line(number)
                status_code = response['status_code']
        self.respond_to_request(status_code, content_type, content)

    def do_PUT(self):
        url = self.path[1:]
        content_type = "application/json"
        content = ''
        status_code = 404
        if url:
            number = parse_url(url)
            if number and type(number) == int:
                content_length = int(self.headers['Content-Length'])
                put_body = self.rfile.read(content_length)
                response = change_line(number, put_body)
                status_code = response['status_code']
        self.respond_to_request(status_code, content_type, content)


host_name = "localhost"
host_port = 8087

server = HTTPServer((host_name, host_port), Server)
print(f"Server Starts - {host_name}:{host_port}")

try:
    server.serve_forever()
except KeyboardInterrupt:
    ...
