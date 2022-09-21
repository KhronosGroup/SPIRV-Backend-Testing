from .config import *
from .models import Revision

from datetime import datetime, timezone, timedelta
import subprocess

def fetch_main_branch_revisions():
    """
    Fetches new commits of the main branch of the tested repository from the
    remote and creates an instance of Revision model for each commit.
    """
    print("Fetching revisions...")

    repository_path = get_tested_repository_path()

    # Hash of the cutoff commit (all main branch commits newer than this one
    # will be fetched).
    cutoff_commit_hash = get_cutoff_commit_hash()
    main_branch_name = get_tested_repository_main_branch_name()

    # Get the latest already fetched revision (commit) and make its hash the
    # cutoff hash.
    latest_main_branch_revision = Revision.objects.filter(
        branch=main_branch_name)
    if latest_main_branch_revision.exists():
        cutoff_commit_hash = latest_main_branch_revision \
                                .latest('date_added').hash

    # Fetch new commits from the remote.
    subprocess.check_output(['git', 'fetch'], cwd=repository_path)

    # Get hashes of the last 100 000 commits.
    latest_commits_hashes = subprocess.check_output(
        ['git', 'log', main_branch_name, '-100000', '--pretty=format:"%H"'],
        cwd=repository_path).decode('utf-8').replace('\"', '').splitlines()

    # Get a list of hashes of revisions that should be created (newer than
    # cutoff commit).
    revisions_to_create_hashes = latest_commits_hashes
    if cutoff_commit_hash in latest_commits_hashes:
        revisions_to_create_hashes = revisions_to_create_hashes \
            [:latest_commits_hashes.index(cutoff_commit_hash)]
    
    # Create revisions.
    for hash in reversed(revisions_to_create_hashes):
        # Get the title of the commit.
        title = subprocess.check_output(
            ['git', 'log', '--format=%B', '-n 1', hash], cwd=repository_path) \
                .decode('utf-8').splitlines()[0][:100]

        # Get the date of the commit.
        unix_timestamp = int(subprocess.check_output(
            ['git', 'show', '-s', '--format=%ct', hash], cwd=repository_path) \
                .decode('utf-8').splitlines()[0])
        date = datetime.fromtimestamp(unix_timestamp, timezone.utc)

        # Get the list of changed files in this commit.
        changed_files = subprocess.check_output(
            ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', hash],
            cwd=repository_path).decode('utf-8')

        # If the commit does not touch relevant files/dirs, set skip as True.
        if 'llvm/lib/Target/SPIRV' in changed_files or \
           'llvm/test/CodeGen/SPIRV' in changed_files:
            skip = False
        else:
            skip = True

        revision = Revision(hash=hash, title=title, branch=main_branch_name,
                            staging=False, date=date, skip=skip)
        revision.save()
        print(revision)

    print(f'Fetched and saved {len(revisions_to_create_hashes)} revisions!')


def fetch_staging_revisions():
    """
    Fetches new top commits from staging branches (Phabricator diffs) from the
    remote and creates an instance of Revision model for each.

    Revisions are created only for commits with [SPIR-V] or [SPIRV] in the
    subject. Commits with [MLIR] in the subject are ignored.
    """
    print("Fetching staging revisions...")

    repository_path = get_tested_repository_path()
    staging_branch_prefix = get_tested_repository_staging_branch_prefix()

    # Fetch new remote branches and prune stale branches.
    subprocess.check_output(['git', 'fetch', '--prune'], cwd=repository_path)

    # Get list of all remote branches (name of the branch followed by subject 
    # of the top commit)
    remote_branches_list = subprocess.check_output(
        ['git', 'branch', '-r', '--format="%(refname:short) %(subject)"'],
        cwd=repository_path).decode('utf-8').replace('\"', '').splitlines()

    for branch_and_subject in remote_branches_list:
        if staging_branch_prefix not in branch_and_subject:
            continue

        if '[SPIR-V]' not in branch_and_subject and \
           '[SPIRV]' not in branch_and_subject:
            continue

        if '[MLIR]' in branch_and_subject or '[mlir]' in branch_and_subject:
            continue

        # Extract the branch name.
        branch_name = branch_and_subject.split(' ')[0]

        # Get the hash of the branch's topmost commit.
        hash = subprocess.check_output(['git', 'rev-parse', branch_name],
            cwd=repository_path).decode('utf-8').splitlines()[0]

        # Get subject of the topmost commit.
        subject = subprocess.check_output(
            ['git', 'log', '--format=%B', '-n 1', hash], cwd=repository_path) \
                .decode('utf-8').splitlines()[0]

        title = branch_name[7:] + ': ' + subject[:60]

        # Get the date of the commit.
        unix_timestamp = int(subprocess.check_output(
            ['git', 'show', '-s', '--format=%ct', hash], cwd=repository_path) \
                .decode('utf-8').splitlines()[0])
        date = datetime.fromtimestamp(unix_timestamp, timezone.utc)

        if date < datetime.now(timezone.utc) - timedelta(days=7):
            continue

        if Revision.objects.filter(hash=hash).exists():
            continue

        revision = Revision(hash=hash, title=title, branch=branch_name,
                            staging=True, date=date, skip=False)
        revision.save()
        print(revision)

    print(f'Fetched and saved staging revisions!')
