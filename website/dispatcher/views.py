from datetime import datetime

from django.http import Http404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import *
from .serializers import *


class JobDetail(APIView):
    """
    Retrieve job details or update job status.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        try:
            return Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        job = self.get_object(pk)
        serializer = JobSerializer(job)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        job = self.get_object(pk)
        serializer = JobDeserializer(job, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Dispatch(APIView):
    """
    Retrieve a queued job to be tested.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        jobs = Job.objects.filter(status=Job.Status.QUEUED).order_by("date_added")
        if jobs.exists():
            return jobs[0]
        else:
            return None

    def post(self, request, format=None):
        job = self.get_object()
        if job is None:
            return Response(status=status.HTTP_204_NO_CONTENT)

        job.status = Job.Status.DISPATCHED
        job.dispatch_date = datetime.now()
        job.dispatch_runner = self.request.user.username
        job.save()

        serializer = JobSerializer(job)
        return Response(serializer.data)


class LitResultDetail(APIView):
    """
    Create a new LIT test result.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_parent_job(self, job_pk):
        try:
            return Job.objects.get(pk=job_pk)
        except Job.DoesNotExist:
            raise Http404

    def post(self, request, job_pk, format=None):
        parent_job = self.get_parent_job(job_pk)

        serializer = LitResultSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            result.parent_job = parent_job
            result.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CtsResultDetail(APIView):
    """
    Create a new CTS test result.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_parent_job(self, job_pk):
        try:
            return Job.objects.get(pk=job_pk)
        except Job.DoesNotExist:
            raise Http404

    def post(self, request, job_pk, format=None):
        parent_job = self.get_parent_job(job_pk)

        serializer = CtsResultSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            result.parent_job = parent_job
            result.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
