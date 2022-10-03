from dataclasses import dataclass
from datetime import datetime


@dataclass
class LITResult:
    test_path: str = None
    passing: bool = None

    def print(self):
        print(f"{self.test_path} (", end="")
        if self.passing:
            print("PASSED", end="")
        else:
            print("FAILED", end="")
        print(")")


@dataclass
class CTSResult:
    test_category: str = None
    test_name: str = None
    passing: bool = False
    timedout: bool = False
    start_time: datetime = None
    end_time: datetime = None
    standard_output: str = None
    standard_error: str = None
    test_executable: str = None
    test_arguments: str = None
    suite_version: str = None
    igc_version: str = None
    neo_version: str = None
    dump_path: str = None

    def print(self):
        print(f"{self.test_category}/{self.test_name} (", end="")
        if self.passing:
            print("PASSED", end="")
        elif self.timedout:
            print("TIMED OUT", end="")
        else:
            print("FAILED", end="")
        print(")")
