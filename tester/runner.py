import subprocess
from config import *


def _checkout_llvm_spirv_backend_revision(hash):
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


def _build_llvm_spirv_backend():
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


def _build_llvm_backend_wrapper():
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
