from django.http import HttpResponse, Http404
from django.template import loader
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator

from datetime import timedelta

from fetcher.models import *
from dispatcher.models import *
from fetcher.config import get_tested_repository_main_branch_name


def index(request):
    template = loader.get_template('index.html')
    context = {'page_title': 'Home'}
    return HttpResponse(template.render(context, request))


def dashboard(request):
    template = loader.get_template('dashboard.html')
    context = {'page_title': 'Dashboard'}
    return HttpResponse(template.render(context, request))


def get_status_for_revision(revision):
    if revision.skip:
        return None
    
    jobs = Job.objects.filter(primary_job=True, revision=revision)
    if not jobs.exists():
        return None
    return jobs[0].status


def commited(request):    
    template = loader.get_template('commited.html')
    
    revisions = Revision.objects.filter(
        staging=False, branch=get_tested_repository_main_branch_name())
    last_tested_revision = None

    for revision in revisions.filter(skip=False):
        if Job.objects.filter \
            (revision=revision, status=Job.Status.COMPLETED).exists():
            last_tested_revision = revision

    paginator = Paginator(revisions, 100)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)

    revision_status_pairs = []
    for revision in page_object:
        revision_status_pairs \
            .append((revision, get_status_for_revision(revision)))

    context = {'page_title': 'Commited', 
               'page_object': page_object,
               'revision_status_pairs': revision_status_pairs, 
               'last_tested_revision': last_tested_revision}
    return HttpResponse(template.render(context, request))


def staging(request):    
    template = loader.get_template('staging.html')

    recently = timezone.now() - timedelta(days=60)
    revisions = Revision.objects.filter(staging=True, date__gte=recently)

    revision_status_pairs = []
    for revision in revisions:
        revision_status_pairs \
            .append((revision, get_status_for_revision(revision)))

    context = {'page_title': 'Staging', 
               'revision_status_pairs': revision_status_pairs}
    return HttpResponse(template.render(context, request))


def queue(request):    
    template = loader.get_template('queue.html')
    jobs = Job.objects.filter(Q(status=Job.Status.QUEUED) | Q(
        status=Job.Status.DISPATCHED) | Q(status=Job.Status.TESTING)) \
            .order_by('date_added')
    context = {'page_title': 'Queue', 'jobs': jobs}
    return HttpResponse(template.render(context, request))


def revision(request, hash):
    template = loader.get_template('revision.html')
    try:
        revision = Revision.objects.get(hash=hash)
    except Revision.DoesNotExist:
        raise Http404('Revision does not exist!')

    jobs = Job.objects.filter(revision=revision)
    context = {'page_title': 'Revision ' + revision.hash[:16], 
               'revision': revision, 
               'jobs': jobs}
    return HttpResponse(template.render(context, request))


def job(request, pk):
    template = loader.get_template('job.html')
    try:
        job = Job.objects.get(pk=pk)
    except Revision.DoesNotExist:
        raise Http404('Job does not exist!')

    lit_results = LitResult.objects.filter(parent_job=job) \
        .order_by('date_added')
    cts_results = CtsResult.objects.filter(parent_job=job) \
        .order_by('date_added')

    lit_results_total = lit_results.count()
    lit_results_passing = lit_results.filter(passing=True).count()
    lit_results_failing = lit_results_total - lit_results_passing

    cts_results_total = cts_results.count()
    cts_results_passing = cts_results.filter(passing=True).count()
    cts_results_failing = cts_results_total - cts_results_passing

    context = {'page_title': 'Job ' + str(job.pk), 'job': job,
               'lit_results': lit_results, 'cts_results': cts_results,
               'lit_results_total': lit_results_total,
               'lit_results_passing': lit_results_passing, 
               'lit_results_failing': lit_results_failing, 
               'cts_results_total': cts_results_total, 
               'cts_results_passing': cts_results_passing, 
               'cts_results_failing': cts_results_failing}
    return HttpResponse(template.render(context, request))


def cts_result(request, pk):
    template = loader.get_template('cts_result.html')
    try:
        result = CtsResult.objects.get(pk=pk)
    except CtsResult.DoesNotExist:
        raise Http404('Result does not exist!')
        
    context = {'page_title': str(result), 'result': result}
    return HttpResponse(template.render(context, request))
