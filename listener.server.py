from http.server import BaseHTTPRequestHandler, HTTPServer
import json


class MyHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        # response
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write('square-ci'.encode('UTF-8'))

    def do_POST(self):
        print('# listener')
        # request
        request_body = self.rfile.read(int(self.headers['Content-Length'])).decode('UTF-8')
        print('receive: ', request_body)
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        response_body = json.dumps({'square-ci': 'test'})
        self.wfile.write(response_body.encode('UTF-8'))
        print('send: ', response_body)
        print()


listener = HTTPServer(('', 6000), MyHandler)
listener.serve_forever()
