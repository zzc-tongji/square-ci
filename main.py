from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import queue
import re
import subprocess

from worker import *
from sleeper import *
from speaker import *

# Queue

# listener +, worker -
queue_alpha = queue.Queue()

# worker +, sleeper -
queue_beta_sleepy = queue.Queue()

# worker +, sleeper +, speaker -
queue_beta = queue.Queue()

# Config

# load
script_path = os.path.split(os.path.realpath(__file__))[0]
with open(script_path + os.sep + 'config.json') as file:
    config = json.loads(file.read())

# check
#
# bash: check_config.sh
for repo in config['repo_list']:
    subprocess.run(
        [
            script_path + os.sep + 'check_config.sh',
            repo['local_directory'],
            repo['script']['test'],
            repo['script']['update']
        ],
        capture_output=True,
        check=True
    )

# Thread

# 4. speaker

speaker = Speaker(config['user_token'], queue_beta)
speaker.start()

# 3. sleeper

sleeper = Sleeper(config['sleeper_delay_second'], queue_beta_sleepy, queue_beta)
sleeper.start()

# 2. worker

worker = Worker(script_path, queue_alpha, queue_beta_sleepy, queue_beta)
worker.start()


# 1. listener

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
        data = json.loads(request_body)
        # match repo
        repo = None
        if 'repository' in data and 'full_name' in data['repository']:
            for r in config['repo_list']:
                if data['repository']['full_name'] == r['remote_path']:
                    repo = r
                    break
        if repo is None:
            self.post_response(json.dumps({'square-ci': 'ignore - repo not set'}))
            return
        # classify GitHub webhooks
        #
        # https://developer.github.com/webhooks/
        # https://developer.github.com/v3/activity/events/types/#pullrequestevent
        # https://developer.github.com/v3/activity/events/types/#pushevent
        classification = None
        if 'action' in data \
                and (data['action'] == 'opened' or data['action'] == 'reopened' or data['action'] == 'synchronize') \
                and 'pull_request' in data \
                and 'number' in data:
            classification = 'alpha-1'
        elif 'action' in data \
                and data['action'] == 'labeled' \
                and 'pull_request' in data \
                and 'head' in data['pull_request'] \
                and 'ref' in data['pull_request']['head'] \
                and 'repo' in data['pull_request']['head'] \
                and 'full_name' in data['pull_request']['head']['repo'] \
                and 'number' in data \
                and 'label' in data \
                and 'name' in data['label'] \
                and data['label']['name'] == 'square-ci':
            classification = 'alpha-2'
        elif 'action' in data \
                and data['action'] == 'closed' \
                and 'pull_request' in data \
                and 'number' in data:
            classification = 'alpha-3'
        elif 'ref' in data \
                and data['ref'] == 'refs/heads/master' \
                and 'head_commit' in data \
                and 'message' in data['head_commit']:
            classification = 'alpha-4'
        #
        if classification == 'alpha-1':
            self.post_response(json.dumps({'square-ci': 'pull requests - opened, reopened, synchronize'}))
            queue_alpha.put({
                'type': classification,
                'repo': repo,
                'issue_number': str(data['number'])
            })
        elif classification == 'alpha-2':
            self.post_response(json.dumps({'square-ci': 'pull requests - labeled as "square-ci"'}))
            queue_alpha.put({
                'type': classification,
                'repo': repo,
                'issue_number': str(data['number']),
                'mergeable': data['pull_request']['mergeable'],
                'merge_from': {
                    'remote_path': data['pull_request']['head']['repo']['full_name'],
                    'branch': data['pull_request']['head']['ref']
                }
            })
        elif classification == 'alpha-3':
            self.post_response(json.dumps({'square-ci': 'pull requests - closed'}))
            queue_alpha.put({
                'type': classification,
                'repo': repo,
                'issue_number': str(data['number'])
            })
        elif classification == 'alpha-4':
            self.post_response(json.dumps({'square-ci': 'pushs - origin/master'}))
            queue_alpha.put({
                'type': classification,
                'repo': repo,
                'issue_number': re.search(r'#\d*', data['head_commit']['message']).group()[1:]
            })
        else:
            self.post_response(json.dumps({'square-ci': 'ignore - webhooks not set'}))

    def post_response(self, body):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(body.encode('UTF-8'))
        print('send: ', body)
        print()


listener = HTTPServer(('', config['listener_port']), MyHandler)
listener.serve_forever()

# blocker

speaker.join()
sleeper.join()
worker.join()
