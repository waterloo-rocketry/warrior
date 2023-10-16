from dataclasses import dataclass, field
from typing import Dict, List, Tuple

ExpectationId = Tuple[str, int] # expectation name, lineno combo

@dataclass
class ExpectationResults:
    id: ExpectationId
    num_checks: int = 0
    num_passes: int = 0
    attempt_data: List[dict] = field(default_factory=list)

@dataclass
class TestResults:
    test: str
    num_executions: int = 0
    num_passes: int = 0
    expectations: Dict[ExpectationId, ExpectationResults] = field(default_factory=dict)

    def simple_analysis(self):
        print(f"{self.test}: {self.num_passes} / {self.num_executions} ({self.num_passes * 100 // self.num_executions}%)")
        for (expectation, line), results in self.expectations.items():
            if results.num_passes == results.num_checks:
                continue
            print(f"  {self.test}:{line} expect.{expectation}: {results.num_passes} / {results.num_checks} ({results.num_passes * 100 // results.num_checks}%)")

@dataclass
class Recorder:
    results: Dict[str, TestResults] = field(default_factory=dict)
    current_test: str = ""

    def record(self, id: ExpectationId, passed: bool, data: dict):
        test_result = self.results[self.current_test]
        if id not in test_result.expectations:
            test_result.expectations[id] = ExpectationResults(id)
        test_result.expectations[id].num_checks += 1
        test_result.expectations[id].num_passes += passed
        test_result.expectations[id].attempt_data.append(data)

    def start_test(self, name: str):
        self.current_test = name
        if name not in self.results:
            self.results[name] = TestResults(name)
        self.results[name].num_executions += 1
        self.results[name].num_passes += 1

    def failed_test(self, name: str):
        self.results[name].num_passes -= 1

recorder = Recorder()
