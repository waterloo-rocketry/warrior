import argparse
import time

from hilt import Hilt

tests = []
# register test function
def test(fn):
    tests.append(fn)
    return fn

parser = argparse.ArgumentParser()
parser.add_argument('port', help='the serial port of the HILT')
args = parser.parse_args()

hilt = Hilt(args.port) # imported by blades

def run():
    while True:
        for test in tests:
            test()
            time.sleep(0.3)
