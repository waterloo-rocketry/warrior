import inspect
from .record import recorder

def get_external_caller():
    caller = inspect.stack()[2]
    return caller.lineno

def equal(actual, expected, tolerance=0):
    id = ("equal", get_external_caller())
    if isinstance(expected, (int, float)):
        diff = abs(actual - expected)
        passed = diff <= tolerance
    else:
        if tolerance != 0:
            raise ValueError(f"Cannot have non-zero tolerance ({tolerance}) when comparing non-numeric values")
        passed = actual == expected
    recorder.record(id, passed, {"actual": actual, "expected": expected, "tolerance": tolerance})
    if not passed:
        raise AssertionError(f"{actual} != {expected}", id)

def non_none(data):
    id = ("non_none", get_external_caller())
    passed = data is not None
    recorder.record(id, passed, {"data": data})
    if not passed:
        raise AssertionError(f"Got None", id)
