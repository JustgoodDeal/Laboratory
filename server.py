from api import add_line, change_line, del_line, get_line, get_posts, filter_content
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from utils import parse_url


class Server(BaseHTTPRequestHandler):
    def respond_to_request(self, status_code, content_type, content):
        """Sends response comprising specified status code and content to a request"""
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        encoding = 'utf-8'
        self.wfile.write(bytes(content, encoding))

    def do_GET(self):
        """Calls corresponding function for handling a GET request depending on the result of URL parsing

        and determines the necessary data for respond to a request.
        If URL is equal to "http://localhost:8087/posts/" - data will be received from function get_posts,
        if matches "http://localhost:8087/posts/<UNIQUE_ID>/" - from get_line.
        If there are get parameters in URL, posts list received from function get_posts will be filtered.
        If URL is equal to "http://localhost:8087/", data needed for displaying the main page will be used.
        If URL is incorrect, status code 404 will be used in response.
        Sends response comprising defined data to the request.
        """
        no_1st_slash_start_index = 1
        url = self.path[no_1st_slash_start_index:]
        if url:
            response = {}
            get_params = ''
            posts_key_word = 'posts'
            get_param = 'per_page'
            if posts_key_word in url and get_param in url:
                get_params_start_index = 6
                get_params = url[get_params_start_index:]
                url = f'{posts_key_word}/'
            unique_id = parse_url(url)
            not_found = 404
            status_code_key = 'status_code'
            if unique_id == not_found:
                status_code = not_found
            elif unique_id:
                response = get_line(unique_id)
                status_code = response[status_code_key]
            else:
                response = get_posts()
                status_code = response[status_code_key]
            content_type = "application/json"
            content_key = 'content'
            content = response.get(content_key, '')
            if get_params:
                content = filter_content(content, get_params)
            content = json.dumps(content)
        else:
            content_type = "text/html"
            content = "<h1>Server</h1>"
            ok = 200
            status_code = ok
        self.respond_to_request(status_code, content_type, content)

    def do_POST(self):
        """Determines the necessary data for respond to a POST request.

        If URL is equal to "http://localhost:8087/posts/", receives these data from function add_line.
        If URL is incorrect, status code 404 will be used in response.
        Sends response comprising defined data to the request.
        """
        url = self.path
        content_type = "application/json"
        suitable_url = "/posts/"
        if url == suitable_url:
            content_length = int(self.headers['Content-Length'])
            post_body = self.rfile.read(content_length)
            response = add_line(post_body)
            content_key = 'content'
            content = response.get(content_key, '')
            status_code_key = 'status_code'
            status_code = response[status_code_key]
        else:
            content = ''
            not_found = 404
            status_code = not_found
        self.respond_to_request(status_code, content_type, content)

    def do_DELETE(self):
        """Determines the necessary data for respond to a DELETE request. Parses URL and if it's equal to

        "http://localhost:8087/posts/<UNIQUE_ID>/", receives these data from function del_line.
        If URL is incorrect, status code 404 will be used in response.
        Sends response comprising defined data to the request.
        """
        no_1st_slash_start_index = 1
        url = self.path[no_1st_slash_start_index:]
        content_type = "application/json"
        content = ''
        not_found = 404
        status_code = not_found
        if url:
            unique_id = parse_url(url)
            if unique_id and unique_id != not_found:
                response = del_line(unique_id)
                status_code_key = 'status_code'
                status_code = response[status_code_key]
        self.respond_to_request(status_code, content_type, content)

    def do_PUT(self):
        """Determines the necessary data for respond to a PUT request. Parses URL and if it's equal to

        "http://localhost:8087/posts/<UNIQUE_ID>/", receives these data from function change_line.
        If URL is incorrect, status code 404 will be used in response.
        Sends response comprising defined data to the request.
        """
        no_1st_slash_start_index = 1
        url = self.path[no_1st_slash_start_index:]
        content_type = "application/json"
        content = ''
        not_found = 404
        status_code = not_found
        if url:
            unique_id = parse_url(url)
            if unique_id and unique_id != not_found:
                content_length = int(self.headers['Content-Length'])
                put_body = self.rfile.read(content_length)
                response = change_line(unique_id, put_body)
                status_code_key = 'status_code'
                status_code = response[status_code_key]
        self.respond_to_request(status_code, content_type, content)


def run_server(host_name, port):
    """Runs the server at a time until shutdown. Pressing buttons on the keyboard will not stop the server"""
    server = HTTPServer((host_name, port), Server)
    print(f"Server Starts - {host_name}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    host = 'localhost'
    port = 8087
    run_server(host, port)
