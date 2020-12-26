from api import add_post, update_post, del_post, get_post, get_posts
from http.server import BaseHTTPRequestHandler, HTTPServer
from utils import parse_url


class Server(BaseHTTPRequestHandler):
    def respond_to_request(self, status_code, content_type, content):
        """Sends response comprising specified status code and content to a request"""
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.end_headers()
        self.wfile.write(bytes(content, "utf-8"))

    def do_GET(self):
        """Calls corresponding function for handling a GET request depending on the result of URL parsing

        and determines the necessary data for respond to a request.
        If URL is equal to "http://localhost:8087/posts/" - data will be received from function get_posts,
        if matches "http://localhost:8087/posts/<UNIQUE_ID>/" - from get_post.
        If URL is equal to "http://localhost:8087/", data needed for displaying the main page will be used.
        If URL is incorrect, status code 404 will be used in response.
        Sends response comprising defined data to the request.
        """
        url = self.path[1:]
        if url:
            response = {}
            id = parse_url(url)
            if id == 404:
                status_code = 404
            elif id:
                response = get_post(id)
                status_code = response['status_code']
            else:
                response = get_posts()
                status_code = response['status_code']
            content_type = "application/json"
            content = response.get('content', '')
        else:
            content_type = "text/html"
            content = "<h1>Server</h1>"
            status_code = 200
        self.respond_to_request(status_code, content_type, content)

    def do_POST(self):
        """Determines the necessary data for respond to a POST request.

        If URL is equal to "http://localhost:8087/posts/", receives these data from function add_post.
        If URL is incorrect, status code 404 will be used in response.
        Sends response comprising defined data to the request.
        """
        url = self.path
        content_type = "application/json"
        if url == "/posts/":
            content_length = int(self.headers['Content-Length'])
            post_body = self.rfile.read(content_length)
            response = add_post(post_body)
            content = response.get('content', '')
            status_code = response['status_code']
        else:
            content = ''
            status_code = 404
        self.respond_to_request(status_code, content_type, content)

    def do_DELETE(self):
        """Determines the necessary data for respond to a DELETE request. Parses URL and if it's equal to

        "http://localhost:8087/posts/<UNIQUE_ID>/", receives these data from function del_post.
        If URL is incorrect, status code 404 will be used in response.
        Sends response comprising defined data to the request.
        """
        url = self.path[1:]
        content_type = "application/json"
        content = ''
        status_code = 404
        if url:
            id = parse_url(url)
            if id and id != 404:
                response = del_post(id)
                status_code = response['status_code']
        self.respond_to_request(status_code, content_type, content)

    def do_PUT(self):
        """Determines the necessary data for respond to a PUT request. Parses URL and if it's equal to

        "http://localhost:8087/posts/<UNIQUE_ID>/", receives these data from function update_post.
        If URL is incorrect, status code 404 will be used in response.
        Sends response comprising defined data to the request.
        """
        url = self.path[1:]
        content_type = "application/json"
        content = ''
        status_code = 404
        if url:
            id = parse_url(url)
            if id and id != 404:
                content_length = int(self.headers['Content-Length'])
                put_body = self.rfile.read(content_length)
                response = update_post(id, put_body)
                status_code = response['status_code']
        self.respond_to_request(status_code, content_type, content)


def run_server(host_name, host_port):
    """Runs the server at a time until shutdown. Pressing buttons on the keyboard will not stop the server"""
    server = HTTPServer((host_name, host_port), Server)
    print(f"Server Starts - {host_name}:{host_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        ...


if __name__ == "__main__":
    run_server("localhost", 8087)
