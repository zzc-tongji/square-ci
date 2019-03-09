from threading import Thread
import json
import requests


class Speaker(Thread):
    def __init__(self, token, queue_beta):
        Thread.__init__(self)
        self.queue_beta = queue_beta
        self.headers = {
            'Content-type': 'text/plain; charset=utf-8',
            'Authorization': 'token ' + token
        }

    def run(self):
        while True:
            item = self.queue_beta.get()
            print('# speaker')
            if item['type'] == 'beta-1':
                # beta-1
                #
                # create a comment
                #
                # https://developer.github.com/v3/issues/comments/#create-a-comment
                #
                # (POST)
                url = 'https://api.github.com/repos/' + item['repo']['remote_path'] \
                      + '/issues/' + item['issue_number'] + '/comments'
                payload = json.dumps({'body': item['body']})
                r = requests.post(url, headers=self.headers, data=payload)
                print('POST:', url)
                print('send:', payload)
                print('receive: ', r.content.decode('UTF-8'))
            elif item['type'] == 'beta-2':
                # beta-2
                #
                # add label "square-ci" (trigger alpha-2 next time by GitHub webhooks)
                #
                # https://developer.github.com/v3/issues/labels/#add-labels-to-an-issue
                #
                # (POST)
                #
                # TODO: act as replace, a bug of GitHub API
                url = 'https://api.github.com/repos/' + item['repo']['remote_path'] \
                      + '/issues/' + item['issue_number']
                payload = json.dumps({'labels': ['square-ci']})
                r = requests.post(url, headers=self.headers, data=payload)
                print('POST:', url)
                print('send:', payload)
                print('receive: ', r.content.decode('UTF-8'))
            elif item['type'] == 'beta-3':
                # beta-3
                #
                # remove label "square-ci"
                #
                # https://developer.github.com/v3/issues/labels/#remove-a-label-from-an-issue
                #
                # (DELETE)
                url = 'https://api.github.com/repos/' + item['repo']['remote_path'] + \
                      '/issues/' + item['issue_number'] + '/labels/square-ci'
                r = requests.delete(url, headers=self.headers)
                print('DELETE:', url)
                print('receive: ', r.content.decode('UTF-8'))
            elif item['type'] == 'beta-4':
                # beta-4
                #
                # merge pull request
                #
                # https://developer.github.com/v3/pulls/#get-a-single-pull-request
                #
                # (GET)
                url = 'https://api.github.com/repos/' + item['repo']['remote_path'] + \
                      '/pulls/' + item['issue_number']
                r = requests.get(url, headers=self.headers)
                data = json.loads(r.content)
                print('GET:', url)
                print('receive: ', r.content.decode('UTF-8'))
                # https://developer.github.com/v3/pulls/#merge-a-pull-request-merge-button
                #
                # (PUT)
                url = 'https://api.github.com/repos/' + item['repo']['remote_path'] + \
                      '/pulls/' + item['issue_number'] + '/merge'
                payload = json.dumps({
                    'commit_title':
                        'Merge pull request #' + item['issue_number'] +
                        ' from ' + data['head']['label'].replace(':', '/'),
                    'commit_message': '',
                    'sha': data['head']['sha'],
                    'merge_method': 'merge'
                })
                r = requests.put(url, headers=self.headers, data=payload)
                print('PUT:', url)
                print('send:', payload)
                print('receive: ', r.content.decode('UTF-8'))
            print()
