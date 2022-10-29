import os
import shutil
import subprocess
from datetime import datetime
from typing import List

from communication import *
from config import *
from results import CTSResult, LITResult


def _checkout_llvm_spirv_backend_revision(hash: str) -> bool:
    """
    Fetches new commits and checkouts the given revision.

    Returns True on success and False on failure.
    """
    project_path = get_tested_repository_build_path()

    # Fetch new commits and branches.
    try:
        run_result = subprocess.run(
            [
                "git",
                "fetch",
            ],
            cwd=project_path,
            timeout=20 * 60,
        )
    except subprocess.TimeoutExpired:
        return False

    if not run_result.returncode == 0:
        return False

    # Checkout the given revision.
    try:
        run_result = subprocess.run(
            [
                "git",
                "checkout",
                hash,
            ],
            cwd=project_path,
            timeout=5 * 60,
        )
    except subprocess.TimeoutExpired:
        return False

    if not run_result.returncode == 0:
        return False

    return True


def _build_llvm_spirv_backend() -> bool:
    """
    Configure and build the LLVM SPIR-V backend.

    Returns True on success and False on failure.
    """
    llvm_build_path = get_tested_repository_build_path()

    # Configure the CMake project.
    try:
        run_result = subprocess.run(
            [
                "cmake",
                "-DCMAKE_BUILD_TYPE=Debug",
                "-DLLVM_EXPERIMENTAL_TARGETS_TO_BUILD=SPIRV",
                "../llvm/",
            ],
            cwd=llvm_build_path,
            timeout=10 * 60,
        )
    except subprocess.TimeoutExpired:
        return False

    if not run_result.returncode == 0:
        return False

    # Build the project.
    try:
        run_result = subprocess.run(
            ["make", "-j4"],
            cwd=llvm_build_path,
            timeout=12 * 60 * 60,
        )
    except subprocess.TimeoutExpired:
        return False

    if not run_result.returncode == 0:
        return False

    return True


def _build_llvm_backend_wrapper() -> bool:
    """
    Configure and build the LLVM backend wrapper.

    Returns True on success and False on failure.
    """
    llvm_build_path = get_tested_repository_build_path()
    backend_wrapper_build_path = get_backend_wrapper_build_path()

    # Configure the CMake project.
    try:
        run_result = subprocess.run(
            [
                "cmake",
                "-DLLVM_DIR=" + llvm_build_path + "lib/cmake/llvm",
                "..",
            ],
            cwd=backend_wrapper_build_path,
            timeout=10 * 60,
        )
    except subprocess.TimeoutExpired:
        return False

    if not run_result.returncode == 0:
        return False

    # Build the project.
    try:
        run_result = subprocess.run(
            ["make", "-j4"],
            cwd=backend_wrapper_build_path,
            timeout=1 * 60 * 60,
        )
    except subprocess.TimeoutExpired:
        return False

    if not run_result.returncode == 0:
        return False

    return True


def _run_all_lit_tests() -> List[LITResult]:
    """
    Run all LLVM SPIR-V LIT tests and create a LITResult for each.
    """
    lit_executable = os.path.join(get_tested_repository_build_path(), "bin/llvm-lit")
    lit_test_directory = os.path.join(
        get_tested_repository_build_path(), "../llvm/test/CodeGen/SPIRV/"
    )

    # Run all lit tests and catch the output.
    run_result = subprocess.run(
        [lit_executable, lit_test_directory, "--max-time", "30"], stdout=subprocess.PIPE
    )
    standard_output = run_result.stdout.decode("utf-8")
    output_result_lines = standard_output[
        standard_output.find("workers --")
        + len("workers --") : standard_output.rfind("********************")
    ].splitlines()[1:-3]

    # Create a LITResult for each line with result.
    results = []
    for line in output_result_lines:
        test_path = line.split(" ")[3]
        passing = not "FAIL" in line
        results.append(LITResult(test_path, passing))

    return results


def _run_cts_test(test_category: str, test_name: str) -> CTSResult:
    """
    Run the specified CTS test and create a CTSResult for the run.
    """
    test_executable = get_cts_test_executable_absolute_path(test_category, test_name)
    test_arguments = get_cts_test_arguments(test_category, test_name)

    # Prepare a temporary directory for dump files.
    dumps_directory_name = (
        test_category + "_" + test_name + "_" + datetime.now().strftime("%Y%m%d%H%M%S")
    )
    dumps_directory_path = os.path.join("/tmp/", dumps_directory_name + "/")
    os.mkdir(dumps_directory_path)

    # Setup the test environment.
    environment = os.environ.copy()
    environment.pop("RUNNER_KEY", None)
    environment["IGC_ShaderDumpEnable"] = "1"
    environment["IGC_ShaderDumpPidDisable"] = "1"
    environment["IGC_DumpToCustomDir"] = dumps_directory_path

    # Start the test.
    start_time = datetime.now()
    try:
        run_result = subprocess.run(
            [test_executable, test_arguments],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(test_executable),
            env=environment,
            timeout=4 * 60 * 60,
        )
        passing = (
            run_result.returncode == 0
            and not "failed" in run_result.stdout.decode("utf-8").lower()
        )
        timedout = False
        standard_output = run_result.stdout.decode("utf-8").replace("\\n", "\n")
        standard_error = run_result.stderr.decode("utf-8").replace("\\n", "\n")
    except subprocess.TimeoutExpired:
        passing = False
        timedout = True
        standard_output = "Test timed out after 4 hours"
        standard_error = "Test timed out after 4 hours"
    end_time = datetime.now()
    # Testing ended.

    # If dump files were generated, delete all irrelevant dumps and make an archive.
    # Delete the dumps directory after.
    if os.listdir(dumps_directory_path):
        run_result = subprocess.run(
            [
                "find",
                ".",
                "-type",
                "f",
                "!",
                "-name",
                "*backend*",
                "-delete",
            ],
            cwd=dumps_directory_path,
            timeout=10 * 60,
        )
        shutil.make_archive(dumps_directory_path, "gztar", dumps_directory_path)
        dumps_path = dumps_directory_path[:-1] + ".tar.gz"
        shutil.rmtree(dumps_directory_path)
    else:
        dumps_path = None
        os.rmdir(dumps_directory_path)

    return CTSResult(
        test_category,
        test_name,
        passing,
        timedout,
        start_time,
        end_time,
        standard_output,
        standard_error,
        test_executable,
        test_arguments,
        get_cts_version(),
        get_igc_version(),
        get_neo_version(),
        dumps_path,
    )


def run_queued_job() -> None:
    """
    Get a queued job from the API, checkout the given revision, build the backend,
    build the wrapper, run the tests, and post the results.

    Returns False in case no testing job was available or current job was cancelled.
    """
    # Get a single queued job from the API. The status of this job is autmatically
    # changed from "Queued" to "Dispatched".
    pk, revision_hash, scheduled_testgroups = get_queued_job()

    if not pk:
        # No job for testing
        return False

    print(f"Testing job {pk} for revision {revision_hash}")

    # Change the status to "Testing".
    update_job_status(pk, JobStatus.TESTING)

    # Checkout the given LLVM commit.
    success = _checkout_llvm_spirv_backend_revision(revision_hash)
    if not success:
        print("Checking out the git commit failed")
        update_job_status(pk, JobStatus.BUILD_FAILED)
        return True

    # Build the LLVM project.
    print("Building the LLVM project...")
    success = _build_llvm_spirv_backend()
    if not success:
        print("Building the LLVM project failed")
        update_job_status(pk, JobStatus.BUILD_FAILED)
        return True

    # Build the backend wrapper.
    print("Building the backend wrapper...")
    success = _build_llvm_backend_wrapper()
    if not success:
        print("Building the backend wrapper failed")
        update_job_status(pk, JobStatus.BUILD_FAILED)
        return True

    # Make sure the job was not cancelled before running the test.
    if get_job_status(pk) != JobStatus.TESTING:
        print("Testing job was cancelled")
        return True

    # If scheduled in this job, run all SPIR-V LIT tests and post the results.
    print("Running LIT tests...")
    if "lit_all" in scheduled_testgroups and scheduled_testgroups["lit_all"]:
        lit_results = _run_all_lit_tests()
        for result in lit_results:
            result.print()
            post_lit_result(pk, result)

    # Run all scheduled OpenCL CTS tests and post the results.
    print("Running OpenCL CTS tests...")
    cts_tests = get_cts_test_list()
    for test in cts_tests:
        # Skip the test if it is not in the category scheduled to run.
        if not ("cts_" + test["test_category"]) in scheduled_testgroups:
            continue

        if not scheduled_testgroups["cts_" + test["test_category"]]:
            continue

        # Make sure the job was not cancelled before running the test.
        if get_job_status(pk) != JobStatus.TESTING:
            print("Testing job was cancelled")
            return False

        result = _run_cts_test(test["test_category"], test["test_name"])
        result.print()
        post_cts_result(pk, result)
        if result.dump_path:
            os.remove(result.dump_path)

    print(f"Finished testing job {pk} for {revision_hash}")
    update_job_status(pk, JobStatus.COMPLETED)
    return True
