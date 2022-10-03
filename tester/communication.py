import os
from datetime import datetime
from enum import Enum

import requests
from requests import adapters, auth

from config import get_api_endpoint
from results import LITResult, CTSResult

API_ENDPOINT = get_api_endpoint()
RUNNER_NAME = os.environ["RUNNER_NAME"]
RUNNER_KEY = os.environ["RUNNER_KEY"]
session = requests.Session()
session.mount(
    API_ENDPOINT,
    adapters.HTTPAdapter(
        max_retries=adapters.Retry(
            total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504]
        )
    ),
)


def get_queued_job():
    """
    Get a tuple representing a job for testing or None.
    Sending this request automatically marks the job as "Dispatched".
    """
    # Deliberately send "POST" request since dispatching changes database data.
    response = session.post(
        url=API_ENDPOINT + "dispatch/", auth=auth.HTTPBasicAuth(RUNNER_NAME, RUNNER_KEY)
    )

    if response.status_code == 204:
        # No jobs for testing available.
        return (None, None, None)

    response.raise_for_status()
    data = response.json()

    pk = data["pk"]
    revision_hash = data["revision_hash"]
    scheduled_testgroups = {}
    for key in data:
        if key.startswith("run_"):
            scheduled_testgroups[key[len("run_") :]] = data[key]

    return (pk, revision_hash, scheduled_testgroups)


class JobStatus(Enum):
    SKIPPED = "S"
    QUEUED = "Q"
    DISPATCHED = "D"
    TESTING = "T"
    COMPLETED = "C"
    BUILD_FAILED = "F"


def get_job_status(pk: int) -> JobStatus:
    """
    Get status of a job with given primary key (pk).
    """
    response = session.get(
        url=API_ENDPOINT + "job/" + str(pk) + "/",
        auth=auth.HTTPBasicAuth(RUNNER_NAME, RUNNER_KEY),
    )

    if response.status_code == 404:
        raise ValueError("Job with specified primary key (pk) does not exist")

    response.raise_for_status()
    data = response.json()
    return JobStatus(data["status"])


def update_job_status(pk: int, status: JobStatus) -> None:
    """
    Update status of a job with given primary key (pk).
    """
    response = session.put(
        url=API_ENDPOINT + "job/" + str(pk) + "/",
        auth=auth.HTTPBasicAuth(RUNNER_NAME, RUNNER_KEY),
        data={"status": status.value},
    )

    if response.status_code == 404:
        raise ValueError("Job with specified primary key (pk) does not exist")

    response.raise_for_status()


def post_lit_result(pk: int, result: LITResult) -> None:
    """
    Post a LIT result for a job with a given primary key (pk).
    """
    response = session.post(
        url=API_ENDPOINT + "job/" + str(pk) + "/lit/",
        auth=auth.HTTPBasicAuth(RUNNER_NAME, RUNNER_KEY),
        data={"test_path": result.test_path, "passing": result.passing},
    )

    if response.status_code == 404:
        raise ValueError("Job with specified primary key (pk) does not exist")

    response.raise_for_status()


def post_cts_result(pk: int, result: CTSResult) -> None:
    """
    Post a CTS result for a job with a given primary key (pk).
    """
    response = session.post(
        url=API_ENDPOINT + "job/" + str(pk) + "/cts/",
        auth=auth.HTTPBasicAuth(RUNNER_NAME, RUNNER_KEY),
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
        files={"dump": open(result.dump_path, "rb")},
    )

    if response.status_code == 404:
        raise ValueError("Job with specified primary key (pk) does not exist")

    response.raise_for_status()