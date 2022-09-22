import json
import os

# Location of the config.json file
CONFIG_FILE_PATH = os.path.join(
    os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))),
    "config.json",
)


def _read_config_value(key):
    with open(CONFIG_FILE_PATH) as config_file:
        config_dict = json.load(config_file)
        if not key in config_dict:
            raise KeyError(f"Key {key} was not found in the config file")

        return config_dict[key]


def get_tested_repository_path():
    """
    Get the absolute path to staging repository under test.
    """
    path = os.path.expanduser(_read_config_value("TESTED_REPOSITORY_PATH"))
    if not os.path.isdir(path):
        raise OSError("Invalid repository under test path")

    return path


def get_tested_repository_main_branch_name():
    """
    Get the name of the main branch in the tested repository.
    """
    return _read_config_value("TESTED_REPOSITORY_MAIN_BRANCH_NAME")


def get_tested_repository_staging_branch_prefix():
    """
    Get the name of the main branch in the tested repository.
    """
    return _read_config_value("TESTED_REPOSITORY_STAGING_BRANCH_PREFIX")


def get_cutoff_commit_hash():
    """
    Get the hash of a cutoff commit (all commits on the main branch newer than
    this one will be fetched)
    """
    return _read_config_value("FETCH_CUTOFF_COMMIT_HASH")
