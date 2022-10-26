from datetime import timedelta

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.template import loader
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_deny
from django.views.decorators.cache import cache_page

from fetcher.config import get_tested_repository_main_branch_name
from fetcher.models import *
from dispatcher.models import *


@xframe_options_deny
def index(request):
    template = loader.get_template("index.html")
    context = {"page_title": "Home"}
    return HttpResponse(template.render(context, request))


@xframe_options_deny
def dashboard(request):
    template = loader.get_template("dashboard.html")
    context = {"page_title": "Dashboard"}
    return HttpResponse(template.render(context, request))


def _get_status_for_revision(revision):
    """
    Get status for revisions's primary job or None if revision is skipped or
    a primary job does not exist.
    """
    if revision.skip:
        return None

    jobs = Job.objects.filter(primary_job=True, revision=revision)
    if not jobs.exists():
        return None
    return jobs[0].status


@xframe_options_deny
@cache_page(60 * 15)
def commited(request):
    template = loader.get_template("commited.html")

    # Retrieve all revisions from the "main" branch.
    revisions = Revision.objects.filter(
        staging=False, branch=get_tested_repository_main_branch_name()
    )

    # Get last tested revision to show at the top of the page.
    last_tested_revision = None
    for revision in revisions.filter(skip=False):
        if Job.objects.filter(revision=revision, status=Job.Status.COMPLETED).exists():
            last_tested_revision = revision

    paginator = Paginator(revisions, 100)
    page_number = request.GET.get("page")
    page_object = paginator.get_page(page_number)

    # Sanitize any strings
    if last_tested_revision:
        last_tested_revision.sanitize()

    for revision in revisions:
        revision.sanitize()

    # Get primary job status for each revision.
    revision_status_pairs = []
    for revision in page_object:
        revision_status_pairs.append((revision, _get_status_for_revision(revision)))

    context = {
        "page_title": "Commited",
        "page_object": page_object,
        "revision_status_pairs": revision_status_pairs,
        "last_tested_revision": last_tested_revision,
    }
    return HttpResponse(template.render(context, request))


@xframe_options_deny
@cache_page(60 * 5)
def staging(request):
    template = loader.get_template("staging.html")

    # Retrieve staging revisions created recently (in the last 60 days).
    recently = timezone.now() - timedelta(days=60)
    revisions = Revision.objects.filter(staging=True, date__gte=recently)

    # Sanitize any strings in the revisions.
    for revision in revisions:
        revision.sanitize()

    # Get primary job status for each revision.
    revision_status_pairs = []
    for revision in revisions:
        revision_status_pairs.append((revision, _get_status_for_revision(revision)))

    context = {"page_title": "Staging", "revision_status_pairs": revision_status_pairs}
    return HttpResponse(template.render(context, request))


@xframe_options_deny
def queue(request):
    template = loader.get_template("queue.html")

    # Retrieve all jobs that are not yet completed.
    jobs = Job.objects.filter(
        Q(status=Job.Status.QUEUED)
        | Q(status=Job.Status.DISPATCHED)
        | Q(status=Job.Status.TESTING)
    ).order_by("date_added")

    # Sanitize any strings in the jobs.
    for job in jobs:
        job.sanitize()

    context = {"page_title": "Queue", "jobs": jobs}
    return HttpResponse(template.render(context, request))


@xframe_options_deny
def revision(request, hash):
    template = loader.get_template("revision.html")

    try:
        revision = Revision.objects.get(hash=hash)
    except Revision.DoesNotExist:
        raise Http404("Revision does not exist!")

    # Get all jobs for the given revision.
    jobs = Job.objects.filter(revision=revision)

    # Sanitize any strings.
    revision.sanitize()

    for job in jobs:
        job.sanitize()

    context = {
        "page_title": "Revision " + revision.hash[:16],
        "revision": revision,
        "jobs": jobs,
    }
    return HttpResponse(template.render(context, request))


@xframe_options_deny
def job(request, pk):
    template = loader.get_template("job.html")

    try:
        job = Job.objects.get(pk=pk)
    except Job.DoesNotExist:
        raise Http404("Job does not exist!")

    # Get all test results for the given job.
    lit_results = LitResult.objects.filter(parent_job=job).order_by("date_added")
    cts_results = CtsResult.objects.filter(parent_job=job).order_by("date_added")

    # Sanitize any strings.
    job.sanitize()

    for result in lit_results:
        result.sanitize()

    for result in cts_results:
        result.sanitize()

    # Calculate passrate stats for all collected results.
    lit_results_total = lit_results.count()
    lit_results_passing = lit_results.filter(passing=True).count()
    lit_results_failing = lit_results_total - lit_results_passing

    cts_results_total = cts_results.count()
    cts_results_passing = cts_results.filter(passing=True).count()
    cts_results_failing = cts_results_total - cts_results_passing

    context = {
        "page_title": "Job " + str(job.pk),
        "job": job,
        "lit_results": lit_results,
        "cts_results": cts_results,
        "lit_results_total": lit_results_total,
        "lit_results_passing": lit_results_passing,
        "lit_results_failing": lit_results_failing,
        "cts_results_total": cts_results_total,
        "cts_results_passing": cts_results_passing,
        "cts_results_failing": cts_results_failing,
    }
    return HttpResponse(template.render(context, request))


@xframe_options_deny
def cts_result(request, pk):
    template = loader.get_template("cts_result.html")

    try:
        result = CtsResult.objects.get(pk=pk)
    except CtsResult.DoesNotExist:
        raise Http404("Result does not exist!")

    # Sanitize any strings.
    result.sanitize()

    context = {
        "page_title": str(result),
        "result": result,
        "test_executable": result.test_executable[
            result.test_executable.find("/test_conformance") :
        ],
    }
    return HttpResponse(template.render(context, request))
