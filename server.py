import api
from http.server import BaseHTTPRequestHandler, HTTPServer
import utils


class Server(BaseHTTPRequestHandler):
    def respond_to_request(self, status_code, content_type, content):
        """Sends response comprising specified status code and content to a request"""
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.end_headers()
        ENCODING = 'utf-8'
        self.wfile.write(bytes(content, ENCODING))

    def do_GET(self):
        """Calls corresponding function for handling a GET request depending on the result of URL parsing

        and determines the necessary data for respond to a request.
        If URL is equal to "http://localhost:8087/posts/" - data will be received from function get_posts,
        if matches "http://localhost:8087/posts/<UNIQUE_ID>/" - from get_post.
        If URL is equal to "http://localhost:8087/", data needed for displaying the main page will be used.
        If URL is incorrect, status code 404 will be used in response.
        Sends response comprising defined data to the request.
        """
        NO_1ST_SLASH_START_INDEX = 1
        url = self.path[NO_1ST_SLASH_START_INDEX:]
        if url:
            response = {}
            unique_id = utils.parse_url(url)
            NOT_FOUND = 404
            STATUS_CODE_KEY = 'status_code'
            if unique_id == NOT_FOUND:
                status_code = NOT_FOUND
            elif unique_id:
                response = api.get_post(unique_id)
                status_code = response[STATUS_CODE_KEY]
            else:
                response = api.get_posts()
                status_code = response[STATUS_CODE_KEY]
            content_type = "application/json"
            CONTENT_KEY = 'content'
            content = response.get(CONTENT_KEY, '')
        else:
            content_type = "text/html"
            content = "<h1>Server</h1>"
            OK = 200
            status_code = OK
        self.respond_to_request(status_code, content_type, content)

    def do_POST(self):
        """Determines the necessary data for respond to a POST request.

        If URL is equal to "http://localhost:8087/posts/", receives these data from function add_post.
        If URL is incorrect, status code 404 will be used in response.
        Sends response comprising defined data to the request.
        """
        url = self.path
        content_type = "application/json"
        SUITABLE_URL = "/posts/"
        if url == SUITABLE_URL:
            content_length = int(self.headers['Content-Length'])
            post_body = self.rfile.read(content_length)
            response = api.add_post(post_body)
            CONTENT_KEY = 'content'
            content = response.get(CONTENT_KEY, '')
            STATUS_CODE_KEY = 'status_code'
            status_code = response[STATUS_CODE_KEY]
        else:
            content = ''
            NOT_FOUND = 404
            status_code = NOT_FOUND
        self.respond_to_request(status_code, content_type, content)

    def do_DELETE(self):
        """Determines the necessary data for respond to a DELETE request. Parses URL and if it's equal to

        "http://localhost:8087/posts/<UNIQUE_ID>/", receives these data from function del_post.
        If URL is incorrect, status code 404 will be used in response.
        Sends response comprising defined data to the request.
        """
        NO_1ST_SLASH_START_INDEX = 1
        url = self.path[NO_1ST_SLASH_START_INDEX:]
        CONTENT_TYPE = "application/json"
        content = ''
        NOT_FOUND = 404
        status_code = NOT_FOUND
        if url:
            unique_id = utils.parse_url(url)
            if unique_id and unique_id != NOT_FOUND:
                response = api.del_post(unique_id)
                STATUS_CODE_KEY = 'status_code'
                status_code = response[STATUS_CODE_KEY]
        self.respond_to_request(status_code, CONTENT_TYPE, content)

    def do_PUT(self):
        """Determines the necessary data for respond to a PUT request. Parses URL and if it's equal to

        "http://localhost:8087/posts/<UNIQUE_ID>/", receives these data from function update_post.
        If URL is incorrect, status code 404 will be used in response.
        Sends response comprising defined data to the request.
        """
        NO_1ST_SLASH_START_INDEX = 1
        url = self.path[NO_1ST_SLASH_START_INDEX:]
        CONTENT_TYPE = "application/json"
        content = ''
        NOT_FOUND = 404
        status_code = NOT_FOUND
        if url:
            unique_id = utils.parse_url(url)
            if unique_id and unique_id != NOT_FOUND:
                content_length = int(self.headers['Content-Length'])
                put_body = self.rfile.read(content_length)
                response = api.update_post(unique_id, put_body)
                STATUS_CODE_KEY = 'status_code'
                status_code = response[STATUS_CODE_KEY]
        self.respond_to_request(status_code, CONTENT_TYPE, content)


def run_server(host_name, port_number):
    """Runs the server at a time until shutdown. Pressing buttons on the keyboard will not stop the server"""
    server = HTTPServer((host_name, port_number), Server)
    print(f"Server Starts - {host_name}:{port_number}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    HOST = 'localhost'
    PORT = 8087
    run_server(HOST, PORT)
