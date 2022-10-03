import os
import json

# Location of the config.json file
CONFIG_FILE_PATH = os.path.join(
    os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))),
    "config.json",
)

# Location of the cts.json file
CTS_FILE_PATH = os.path.join(
    os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))), "cts.json"
)


def _read_config_value(key):
    with open(CONFIG_FILE_PATH) as config_file:
        config_dict = json.load(config_file)
        if not key in config_dict:
            raise KeyError(f"Key {key} was not found in the config file")

        return config_dict[key]


def get_cts_build_path():
    """
    Get the absolute path to the OpenCL CTS build directory.
    """
    path = os.path.expanduser(_read_config_value("CTS_BUILD_PATH"))
    if not os.path.isdir(path):
        raise OSError("Invalid CTS build directory path")

    return path


def get_cts_test_list():
    """
    Get list of all OpenCL CTS tests.
    """
    with open(CTS_FILE_PATH) as cts_file:
        cts_test_list = json.load(cts_file)
        return cts_test_list


def get_cts_test_executable_relative_path(test_category, test_name):
    """
    Get the executable relative path for the given OpenCL CTS test.
    """
    test_list = get_cts_test_list()
    for test in test_list:
        if test["test_category"] == test_category and test["test_name"] == test_name:
            return test["executable_path"]

    raise KeyError(f"Test {test_category}/{test_name} definition was not found")


def get_cts_test_executable_absolute_path(test_category, test_name):
    """
    Get the executable absolute path for the given OpenCL CTS test.
    """
    build_path = get_cts_build_path()
    test_relative_path = get_cts_test_executable_relative_path(test_category, test_name)
    test_absolute_path = os.path.join(build_path, test_relative_path)
    return test_absolute_path


def get_cts_test_arguments(test_category, test_name):
    """
    Get CLI arguments required to run the given OpenCL CTS test.
    """
    test_list = get_cts_test_list()
    for test in test_list:
        if test["test_category"] == test_category and test["test_name"] == test_name:
            return test["arguments"]

    raise KeyError(f"Test {test_category}/{test_name} definition was not found")


def get_tested_repository_build_path():
    """
    Get the absolute path to the tested repository build directory.
    """
    path = os.path.expanduser(_read_config_value("TESTED_REPOSITORY_BUILD_PATH"))
    if not os.path.isdir(path):
        raise OSError("Invalid tested repository build directory path")

    return path


def get_backend_wrapper_build_path():
    """
    Get the absolute path to the backend wrapper build directory.
    """
    path = os.path.expanduser(_read_config_value("BACKEND_WRAPPER_BUILD_PATH"))
    if not os.path.isdir(path):
        raise OSError("Invalid backend wrapper build directory path")

    return path


def get_api_endpoint():
    """
    Get the address of the API endpoint.
    """
    endpoint = _read_config_value("API_ENDPOINT")
    if not endpoint:
        raise ValueError("API endpoint not defined")

    return endpoint


def get_igc_version():
    """
    Get the version of the Intel Graphics Compiler.
    """
    return _read_config_value("IGC_VERSION")


def get_neo_version():
    """
    Get the version of the Intel Graphics Compute Runtime.
    """
    return _read_config_value("NEO_VERSION")


def get_cts_version():
    """
    Get the version of the OpenCL CTS test suite.
    """
    return _read_config_value("CTS_VERSION")
