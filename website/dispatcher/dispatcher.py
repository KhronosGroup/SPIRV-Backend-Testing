from fetcher.models import Revision
from .models import Job

def create_jobs():
    """
    Creates primary jobs (running all tests from all test suites) for newly
    fetched revisions.
    """
    print('Creating jobs...')

    # Get all revisions which should not be skipped (having relevant changes).
    revisions = Revision.objects.filter(skip=False).order_by('date')

    for revision in revisions:
        # Do not create a new job for revisions which already have a primary
        # job (main job running all tests from all test suites).
        if Job.objects.filter(revision=revision, primary_job=True).exists():
            continue

        job = Job(revision=revision, primary_job=True,
                  status=Job.Status.QUEUED)
        print(job)
        job.save()

    print('Finished creating jobs!')
