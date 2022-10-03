import argparse
from time import sleep

from runner import run_queued_job


def run_test_bot():
    # Infinite test loop: get a testing job, build the environment, run the tests,
    # and submit the results.
    while True:
        job_was_available = run_queued_job()
        if not job_was_available:
            # No queued job was available or a job was cancelled. Sleep for 3 minutes
            # to not send API requests continuously.
            sleep(3 * 60)


def main():
    # Parse CLI arguments.
    parser = argparse.ArgumentParser(
        prog="tester",
        description="Automated test runner for SPIR-V backend offline and online tests",
    )
    parser.add_argument(
        "-b",
        "--bottest",
        action="store_true",
        default=False,
        help="Test queued jobs (in a loop)",
    )
    arguments = parser.parse_args()

    if arguments.bottest:
        run_test_bot()


if __name__ == "__main__":
    main()
