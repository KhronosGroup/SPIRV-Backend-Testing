import argparse
import sys
from time import sleep
from communication import create_session
from runner import test_remote_queued_job, test_local_full_job


def run_automated_testing(api_endpoint: str, runner_name: str, runner_key: str) -> None:
    # Set the API endpoint and create a new session with provided auth key.
    create_session(api_endpoint, runner_name, runner_key)

    # Infinite test loop: get a testing job, build the environment, run the tests,
    # and submit the results.
    while True:
        if not test_remote_queued_job():
            # No queued job was available or a job was cancelled. Sleep for 5 minutes
            # to not send API requests continuously.
            sleep(5 * 60)


def run_manual_testing() -> None:
    # Runs all available tests on a local HEAD revision of the backend.
    test_local_full_job()


def main():
    # Parse CLI arguments.
    parser = argparse.ArgumentParser(
        prog="tester",
        description="Automated test runner for SPIR-V backend offline and online tests",
    )

    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        choices=["manual", "auto"],
        default="manual",
        help="""manual (default) - run all tests on the local HEAD revision of the backend and print results;
                auto - run a queued test job from remote API, print progress, and publish results""",
    )
    parser.add_argument(
        "--api",
        type=str,
        required="auto" in sys.argv,
        default=None,
        help="API endpoint for fetching jobs and publishing results",
    )
    parser.add_argument(
        "--runnername",
        type=str,
        required="auto" in sys.argv,
        default=None,
        help="name of this automated test runner used for authentication",
    )
    parser.add_argument(
        "--runnerkey",
        type=str,
        required="auto" in sys.argv,
        default=None,
        help="key of this automated test runner used for authentication",
    )
    arguments = parser.parse_args()

    if arguments.mode == "auto":
        print("Testing all queued jobs in automated testing mode...")
        run_automated_testing()
    elif arguments.mode == "manual":
        print("Testing a local HEAD revision of the backend...")
        run_manual_testing()


if __name__ == "__main__":
    main()
