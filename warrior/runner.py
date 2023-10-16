import time
import sys
from . import expect
from .record import recorder
from . import hilt
from .ui import ui

class TestRunner:
    def __init__(self):
        self.tests = []
        self.test_conditions = {}
        self.nominal_tests = []

    # use as decorator
    def __call__(self, fn):
        self.tests.append(fn)
        return fn

    # nominal tests are executed between every other, and must pass to continue
    def nominal(self, fn):
        self.nominal_tests.append(fn)
        return fn

    def conditional(self, condition):
        def wrap(fn):
            self.tests.append(fn)
            self.test_conditions[fn.__name__] = condition
            return fn
        return wrap

    def execute(self, test):
        recorder.start_test(test.__name__)
        try:
            ui.print_log(f"Executing {test.__name__}...")
            test()
            ui.print_log(" PASSED!\n")
            return True
        except AssertionError as e:
            recorder.failed_test(test.__name__)
            ui.print_log(f" FAILED! {e.args[0]} at line {e.args[1][1]}\n")
        return False

    def run(self):
        ui.setup()
        try:
            while True:
                for test in self.tests:
                    condition = self.test_conditions.get(test.__name__, True)
                    if hasattr(condition, "__call__"):
                        condition = condition()
                    if not condition:
                        ui.print_log(f"Skipping {test.__name__}.\n")
                        continue
                    for nominal in self.nominal_tests:
                        while not self.execute(nominal):
                            time.sleep(1)
                    self.execute(test)
        except KeyboardInterrupt:
            # Run nominal tests to clean up
            for nominal in self.nominal_tests:
                self.execute(nominal)
            print()
            print()
            for result in recorder.results.values():
                result.simple_analysis()

test = TestRunner()
run = test.run
