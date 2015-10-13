from threading import Timer
import time

class RepeatedTimer(object):
    def __init__(self, interval, function, count, *args):
        self._timer = None
        self.interval = interval
        self.function = function
        self.count = count
        self.args = args
        self.is_running = False


    def _run(self):
        self.is_running = False
        self.start()
        if self.count > 0:
            self.function(*self.args)
            self.count -= 1
        else:
            self.stop()

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

    def wait(self):
        while self.is_running:
            time.sleep(1)

def hello(client, server):
    print client, ":", server

def _test():
    rt = RepeatedTimer(1, hello, 5, "1", "2")
    rt.start()
    rt.wait()

    rt1 = RepeatedTimer(1, hello, 5, "3", "4")
    rt1.start()
    rt1.wait()

#_test()
