from threading import Thread
import os
import subprocess


class Worker(Thread):
    def __init__(self, script_path, queue_alpha, queue_beta_sleepy, queue_beta):
        Thread.__init__(self)
        self.script_path = script_path
        self.queue_alpha = queue_alpha
        self.queue_beta_sleepy = queue_beta_sleepy
        self.queue_beta = queue_beta

    def run(self):
        while True:
            item = self.queue_alpha.get()
            if item['type'] == 'alpha-1':
                # GitHub webhooks: pull requests - opened, reopened, synchronize
                #
                # conflict detection (GitHub) result not available
                #
                # add label "square-ci"
                # wait for conflict detection result (GitHub)
                self.queue_beta_sleepy.put({
                    'type': 'beta-2',
                    'repo': item['repo'],
                    'issue_number': item['issue_number']
                })
            elif item['type'] == 'alpha-2':
                # GitHub webhooks: pull requests - labeled as "square-ci"
                if item['mergeable'] is None:
                    # conflict detection (GitHub) result not available
                    #
                    # remove label "square-ci"
                    self.queue_beta.put({
                        'type': 'beta-3',
                        'repo': item['repo'],
                        'issue_number': item['issue_number']
                    })
                    # add label "square-ci"
                    # wait for conflict detection result (GitHub)
                    self.queue_beta_sleepy.put({
                        'type': 'beta-2',
                        'repo': item['repo'],
                        'issue_number': item['issue_number']
                    })
                    continue
                elif item['mergeable'] is False:
                    # conflict detected
                    #
                    # remove label "square-ci"
                    self.queue_beta.put({
                        'type': 'beta-3',
                        'repo': item['repo'],
                        'issue_number': item['issue_number']
                    })
                    # create a comment (conflict)
                    self.queue_beta.put({
                        'type': 'beta-1',
                        'repo': item['repo'],
                        'issue_number': item['issue_number'],
                        'body': '### Square CI\n\nstatus\n\n```\nCONFLICTED\n```\n'
                    })
                    continue
                # bash: execute_test.sh
                result = subprocess.run(
                    [
                        self.script_path + os.sep + 'execute_test.sh',
                        item['repo']['local_directory'],
                        item['repo']['script']['test'],
                        'https://github.com/' + item['merge_from']['remote_path'] + '.git',
                        item['merge_from']['branch']
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT
                )
                if result.returncode == 0:
                    # create a comment (passed)
                    self.queue_beta.put({
                        'type': 'beta-1',
                        'repo': item['repo'],
                        'issue_number': item['issue_number'],
                        'body': '### Square CI\n\nstatus\n\n```\nPASSED\n```\n\noutput\n\n```'
                                + result.stdout.decode('UTF-8')
                                + '\n```\n'
                    })
                    # merge pull request
                    self.queue_beta.put({
                        'type': 'beta-4',
                        'repo': item['repo'],
                        'issue_number': item['issue_number'],
                    })
                else:
                    # create a comment (failed)
                    self.queue_beta.put({
                        'type': 'beta-1',
                        'repo': item['repo'],
                        'issue_number': item['issue_number'],
                        'body': '### Square CI\n\nstatus\n\n```\nFAILED\n```\n\noutput\n\n```'
                                + result.stdout.decode('UTF-8')
                                + '\n```\n'
                    })
                    # remove label "square-ci"
                    self.queue_beta.put({
                        'type': 'beta-3',
                        'repo': item['repo'],
                        'issue_number': item['issue_number']
                    })
            elif item['type'] == 'alpha-3':
                # GitHub webhooks: pull requests - closed
                #
                # remove label "square-ci"
                self.queue_beta_sleepy.put({
                    'type': 'beta-3',
                    'repo': item['repo'],
                    'issue_number': item['issue_number']
                })
            elif item['type'] == 'alpha-4':
                # GitHub webhooks: pushs - origin / master
                #
                # bash: update
                path = self.script_path + os.sep + 'target' + os.sep + item['repo']['local_directory']
                result = subprocess.run(
                    'cd ' + path + ' && ' + '.' + os.sep + item['repo']['script']['update'],
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT
                )
                # create a comment (updated)
                self.queue_beta.put({
                    'type': 'beta-1',
                    'repo': item['repo'],
                    'issue_number': item['issue_number'],
                    'body': '### Square CI\n\nstatus\n\n```\nUPDATED\n```\n\noutput\n\n```'
                            + result.stdout.decode('UTF-8')
                            + '\n```\n'
                })
