import sys
from typing import IO

STDOUT = sys.stdout


class BufferedStream:
    def __init__(self, stream: IO):
        self.stream = stream
        self.data = []

    def write(self, data):
        self.data.append(data)

    def writelines(self, datas):
        self.data += datas

    def read(self) -> str:
        return ''.join(self.data)

    def flush(self):
        for data in self.data:
            self.stream.write(data)

    def __getattr__(self, attr):
        return getattr(self.stream, attr)


def disable_stdout():
    sys.stdout = BufferedStream(sys.stdout)


def enable_stdout():
    sys.stdout = STDOUT
