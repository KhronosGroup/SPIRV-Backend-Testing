from datetime import datetime
from enum import Enum
import time

import requests
from requests import adapters, auth

from results import LITResult, CTSResult


def retry_request(request_function, **kwargs):
    """
    Tries to send a given request in various time intervals.
    """
    for time_between_tries in [0, 60, 3600, 7200]:
        try:
            time.sleep(time_between_tries)
            response = request_function(**kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError:
            print(f"Connection error after {str(time_between_tries)} seconds!")
        except requests.exceptions.HTTPError as exception:
            if exception.response.status_code == 404:
                return exception.response

            print(f"HTTP error after {str(time_between_tries)} seconds!")
    raise


class JobStatus(Enum):
    SKIPPED = "S"
    QUEUED = "Q"
    DISPATCHED = "D"
    TESTING = "T"
    COMPLETED = "C"
    BUILD_FAILED = "F"


class APISession:
    def __init__(self, api_endpoint: str, runner_name: str, runner_key: str) -> None:
        """
        Create a new session with the API.
        """
        self.API_ENDPOINT = api_endpoint
        self.SESSION = requests.Session()
        self.SESSION.headers = {"User-Agent": "Mozilla/5.0"}
        self.SESSION.auth = auth.HTTPBasicAuth(runner_name, runner_key)
        self.SESSION.mount(
            api_endpoint,
            adapters.HTTPAdapter(),
        )

    def get_queued_job(self):
        """
        Get a tuple representing a job for testing or None.
        Sending this request automatically marks the job as "Dispatched".
        """
        # Deliberately send "POST" request since dispatching changes database data.
        response = retry_request(self.SESSION.post, url=self.API_ENDPOINT + "dispatch/")

        if response.status_code == 204:
            # No jobs for testing available.
            return (None, None, None)

        data = response.json()

        pk = data["pk"]
        revision_hash = data["revision_hash"]
        scheduled_testgroups = {}
        for key in data:
            if key.startswith("run_"):
                scheduled_testgroups[key[len("run_") :]] = data[key]

        return (pk, revision_hash, scheduled_testgroups)

    def get_job_status(self, pk: int) -> JobStatus:
        """
        Get status of a job with given primary key (pk).
        """
        response = retry_request(
            self.SESSION.get, url=self.API_ENDPOINT + "job/" + str(pk) + "/"
        )

        if response.status_code == 404:
            raise ValueError("Job with specified primary key (pk) does not exist")

        data = response.json()
        return JobStatus(data["status"])

    def update_job_status(self, pk: int, status: JobStatus) -> None:
        """
        Update status of a job with given primary key (pk).
        """
        response = retry_request(
            self.SESSION.put,
            url=self.API_ENDPOINT + "job/" + str(pk) + "/",
            data={"status": status.value},
        )

        if response.status_code == 404:
            raise ValueError("Job with specified primary key (pk) does not exist")

        response.raise_for_status()

    def post_lit_result(self, pk: int, result: LITResult) -> None:
        """
        Post a LIT result for a job with a given primary key (pk).
        """
        response = retry_request(
            self.SESSION.post,
            url=self.API_ENDPOINT + "job/" + str(pk) + "/lit/",
            data={"test_path": result.test_path, "passing": result.passing},
        )

        if response.status_code == 404:
            raise ValueError("Job with specified primary key (pk) does not exist")

    def post_cts_result(self, pk: int, result: CTSResult) -> None:
        """
        Post a CTS result for a job with a given primary key (pk).
        """
        files = {}
        if result.dump_path:
            files = {"dump": open(result.dump_path, "rb")}

        response = retry_request(
            self.SESSION.post,
            url=self.API_ENDPOINT + "job/" + str(pk) + "/cts/",
            data={
                "test_category": result.test_category,
                "test_name": result.test_name,
                "timedout": result.timedout,
                "passing": result.passing,
                "start_time": datetime.isoformat(result.start_time)[:-3] + "Z",
                "end_time": datetime.isoformat(result.end_time)[:-3] + "Z",
                "standard_output": result.standard_output,
                "standard_error": result.standard_error,
                "test_executable": result.test_executable,
                "test_arguments": result.test_arguments,
                "suite_version": result.suite_version,
                "igc_version": result.igc_version,
                "neo_version": result.neo_version,
            },
            files=files,
        )

        if response.status_code == 404:
            raise ValueError("Job with specified primary key (pk) does not exist")
