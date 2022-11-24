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
    for revision in revisions.filter(skip=False).order_by("date_added"):
        if Job.objects.filter(revision=revision, status=Job.Status.COMPLETED).exists():
            last_tested_revision = revision

    paginator = Paginator(revisions, 100)
    page_number = request.GET.get("page")
    page_object = paginator.get_page(page_number)

    # Sanitize any strings
    if last_tested_revision:
        last_tested_revision.sanitize()

    for revision in page_object:
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


def _get_latest_main_branch_primary_job():
    """
    Get the latest main branch revision's primary completed job.
    """
    latest_revision = Revision.objects.filter(
        skip=False, branch=get_tested_repository_main_branch_name()
    )
    if latest_revision.exists():
        return Job.objects.filter(
            revision=latest_revision.latest("date_added"),
            primary_job=True,
            status=Job.Status.COMPLETED,
        ).first()

    return None


@xframe_options_deny
def queue(request):
    template = loader.get_template("queue.html")

    # Retrieve all jobs that are not yet completed.
    jobs = Job.objects.filter(
        Q(status=Job.Status.QUEUED)
        | Q(status=Job.Status.DISPATCHED)
        | Q(status=Job.Status.TESTING)
    ).order_by("date_added")

    # Get a job to compare the queued jobs to.
    latest_main_branch_primary_job = _get_latest_main_branch_primary_job()

    # Sanitize any strings in the jobs.
    for job in jobs:
        job.sanitize()

    if latest_main_branch_primary_job:
        latest_main_branch_primary_job.sanitize()

    context = {
        "page_title": "Queue",
        "jobs": jobs,
        "latest_main_branch_primary_job": latest_main_branch_primary_job,
    }
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

    # Get a job to compare the given job to.
    latest_main_branch_primary_job = _get_latest_main_branch_primary_job()

    # Sanitize any strings.
    revision.sanitize()

    if latest_main_branch_primary_job:
        latest_main_branch_primary_job.sanitize()

    for job in jobs:
        job.sanitize()

    context = {
        "page_title": "Revision " + revision.hash[:16],
        "revision": revision,
        "jobs": jobs,
        "latest_main_branch_primary_job": latest_main_branch_primary_job,
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
def job_compare(request, pk1, pk2):
    template = loader.get_template("job_compare.html")

    try:
        job1 = Job.objects.get(pk=pk1)
        job2 = Job.objects.get(pk=pk2)
    except Job.DoesNotExist:
        raise Http404("Job does not exist!")

    # Collect recent completed jobs available for comparison.
    recently = timezone.now() - timedelta(days=60)
    available_comparison_jobs = Job.objects.filter(
        primary_job=True, status=Job.Status.COMPLETED, date_added__gte=recently
    )

    # Get all test results for job 1.
    job1_lit_results = LitResult.objects.filter(parent_job=job1).order_by("date_added")
    job1_cts_results = CtsResult.objects.filter(parent_job=job1).order_by("date_added")

    # Get all test results for job 2.
    job2_lit_results = LitResult.objects.filter(parent_job=job2).order_by("date_added")
    job2_cts_results = CtsResult.objects.filter(parent_job=job2).order_by("date_added")

    # Sanitize any strings.
    for job in available_comparison_jobs:
        job.sanitize()

    job1.sanitize()
    job2.sanitize()

    # Calculate passrate stats for job 1.
    job1_lit_results_total = job1_lit_results.count()
    job1_lit_results_passing = job1_lit_results.filter(passing=True).count()
    job1_lit_results_failing = job1_lit_results_total - job1_lit_results_passing

    job1_cts_results_total = job1_cts_results.count()
    job1_cts_results_passing = job1_cts_results.filter(passing=True).count()
    job1_cts_results_failing = job1_cts_results_total - job1_cts_results_passing

    # Calculate passrate stats for job 2.
    job2_lit_results_total = job2_lit_results.count()
    job2_lit_results_passing = job2_lit_results.filter(passing=True).count()
    job2_lit_results_failing = job2_lit_results_total - job2_lit_results_passing

    job2_cts_results_total = job2_cts_results.count()
    job2_cts_results_passing = job2_cts_results.filter(passing=True).count()
    job2_cts_results_failing = job2_cts_results_total - job2_cts_results_passing

    # Collect LIT test result pairs for job 1 and job 2.
    lit_result_pairs = []
    job2_lit_results_paired = []
    for job1_result in job1_lit_results:
        job2_result = job2_lit_results.filter(test_path=job1_result.test_path).first()
        lit_result_pairs.append((job1_result, job2_result))
        job2_lit_results_paired.append(job2_result)

    for job2_result in job2_lit_results:
        if not job2_result in job2_lit_results_paired:
            lit_result_pairs.append((None, job2_result))

    # Collect CTS test result pairs for job 1 and job 2.
    cts_result_pairs = []
    job2_cts_results_paired = []
    for job1_result in job1_cts_results:
        job2_result = job2_cts_results.filter(
            test_category=job1_result.test_category, test_name=job1_result.test_name
        ).first()
        cts_result_pairs.append((job1_result, job2_result))
        job2_cts_results_paired.append(job2_result)

    for job2_result in job2_cts_results:
        if not job2_result in job2_cts_results_paired:
            cts_result_pairs.append((None, job2_result))

    context = {
        "page_title": "Job " + str(job1.pk) + ":" + str(job2.pk) + " compare",
        "job1": job1,
        "job2": job2,
        "lit_result_pairs": lit_result_pairs,
        "cts_result_pairs": cts_result_pairs,
        "job1_lit_results_total": job1_lit_results_total,
        "job1_lit_results_passing": job1_lit_results_passing,
        "job1_lit_results_failing": job1_lit_results_failing,
        "job1_cts_results_total": job1_cts_results_total,
        "job1_cts_results_passing": job1_cts_results_passing,
        "job1_cts_results_failing": job1_cts_results_failing,
        "job2_lit_results_total": job2_lit_results_total,
        "job2_lit_results_passing": job2_lit_results_passing,
        "job2_lit_results_failing": job2_lit_results_failing,
        "job2_cts_results_total": job2_cts_results_total,
        "job2_cts_results_passing": job2_cts_results_passing,
        "job2_cts_results_failing": job2_cts_results_failing,
        "available_comparison_jobs": available_comparison_jobs,
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
