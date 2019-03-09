from threading import Thread
import time


class Sleeper(Thread):
    def __init__(self, sleeper_delay_second, queue_beta_sleepy, queue_beta):
        Thread.__init__(self)
        self.sleeper_delay_second = sleeper_delay_second
        self.queue_beta_sleepy = queue_beta_sleepy
        self.queue_beta = queue_beta

    def run(self):
        while True:
            item = self.queue_beta_sleepy.get()
            time.sleep(self.sleeper_delay_second)
            self.queue_beta.put(item)
