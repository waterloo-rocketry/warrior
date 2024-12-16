import shutil
import threading

class UI:
    def __init__(self):
        self.dims = shutil.get_terminal_size()

        self.can_height = self.dims.lines // 3 * 2
        self.log_height = self.dims.lines - self.can_height

        self.can_buf = [""]
        self.log_buf = [""]

        self.lock = threading.Lock()

    def setup(self):
        print("\n" * self.dims.lines, end='') # clear screen

    def print_can(self, s):
        with self.lock:
            if len(s) > self.dims.columns - 1:
                s = s[:self.dims.columns - 1] + "\n"
            start, *lines = s.split("\n")
            self.can_buf[-1] += start
            self.can_buf += lines
            self.can_buf = self.can_buf[-self.can_height:]
            print(f"\033[{self.can_height};1H\033[1J\033[1;1H", end='')
            print('\n'.join(self.can_buf), end='', flush=True)

    def print_log(self, s):
        with self.lock:
            start, *lines = s.split("\n")
            self.log_buf[-1] += start
            self.log_buf += lines
            self.log_buf = self.log_buf[-self.log_height:]
            print(f"\033[{self.can_height + 1};1H\033[0J\033[{self.can_height + 1};1H", end='')
            print('\n'.join(self.log_buf), end='', flush=True)

ui = UI()
