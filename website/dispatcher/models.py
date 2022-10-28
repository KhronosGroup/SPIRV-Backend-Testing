from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from fetcher.models import Revision
import bleach


# Model representing a test plan to be executed on a runner
class Job(models.Model):
    revision = models.ForeignKey(Revision, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    primary_job = models.BooleanField(default=False)
    run_lit_all = models.BooleanField(default=True)
    run_cts_api = models.BooleanField(default=True)
    run_cts_basic = models.BooleanField(default=True)
    run_cts_atomics = models.BooleanField(default=True)
    run_cts_buffers = models.BooleanField(default=True)
    run_cts_commonfns = models.BooleanField(default=True)
    run_cts_compiler = models.BooleanField(default=True)
    run_cts_computeinfo = models.BooleanField(default=True)
    run_cts_contractions = models.BooleanField(default=True)
    run_cts_device_partition = models.BooleanField(default=True)
    run_cts_events = models.BooleanField(default=True)
    run_cts_geometrics = models.BooleanField(default=True)
    run_cts_half = models.BooleanField(default=True)
    run_cts_integer_ops = models.BooleanField(default=True)
    run_cts_mem_host_flags = models.BooleanField(default=True)
    run_cts_multiple_device_context = models.BooleanField(default=True)
    run_cts_printf = models.BooleanField(default=True)
    run_cts_profiling = models.BooleanField(default=True)
    run_cts_relationals = models.BooleanField(default=True)
    run_cts_select = models.BooleanField(default=True)
    run_cts_thread_dimensions = models.BooleanField(default=True)
    run_cts_vectors = models.BooleanField(default=True)
    run_cts_c11_atomics = models.BooleanField(default=True)
    run_cts_device_execution = models.BooleanField(default=True)
    run_cts_non_uniform_work_group = models.BooleanField(default=True)
    run_cts_generic_address_space = models.BooleanField(default=True)
    run_cts_subgroups = models.BooleanField(default=True)
    run_cts_workgroups = models.BooleanField(default=True)
    run_cts_pipes = models.BooleanField(default=True)
    run_cts_device_timer = models.BooleanField(default=True)
    run_cts_spirv_new = models.BooleanField(default=True)
    run_cts_math_brute_force = models.BooleanField(default=True)
    run_cts_SVM = models.BooleanField(default=True)
    run_cts_clCopyImage = models.BooleanField(default=True)
    run_cts_clFillImage = models.BooleanField(default=True)
    run_cts_clGetInfo = models.BooleanField(default=True)
    run_cts_clReadWriteImage = models.BooleanField(default=True)
    run_cts_kernel_image_methods = models.BooleanField(default=True)
    run_cts_kernel_read_write = models.BooleanField(default=True)
    run_cts_samplerlessReads = models.BooleanField(default=True)

    class Status(models.TextChoices):
        SKIPPED = "S", _("Skipped")
        QUEUED = "Q", _("Queued")
        DISPATCHED = "D", _("Dispatched")
        TESTING = "T", _("Testing")
        COMPLETED = "C", _("Completed")
        BUILD_FAILED = "F", _("Build failed")

    status = models.CharField(
        max_length=1, choices=Status.choices, default=Status.QUEUED
    )
    status_details = models.TextField(blank=True)
    dispatch_date = models.DateTimeField(blank=True, null=True)
    dispatch_runner = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return (
            "Job " + str(self.pk)
            + " (" + self.status + ")"
            + " for " + self.revision.hash[:16] + " / " + self.revision.title[:80]
        )

    class Meta:
        ordering = ["-date_added"]

    def sanitize(self):
        """
        Sanitizes the object's data before passing to a view.
        """
        self.revision.sanitize()


# Model representing a LIT test result
class LitResult(models.Model):
    parent_job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    test_path = models.CharField(max_length=200)
    passing = models.BooleanField(default=False)

    def __str__(self):
        return (
            'LIT "' + self.test_path
            + '" (' + ("PASS" if self.passing else "FAIL") + ") "
            + " for job " + str(self.parent_job.pk)
        )

    class Meta:
        ordering = ["-date_added"]

    def sanitize(self):
        """
        Sanitizes the object's data before passing to a view.
        """
        self.parent_job.sanitize()

# Model representing a CTS test result
class CtsResult(models.Model):
    parent_job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    test_category = models.CharField(max_length=50)
    test_name = models.CharField(max_length=200)
    passing = models.BooleanField(default=False)
    timedout = models.BooleanField(default=False)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    standard_output = models.TextField(blank=True)
    standard_error = models.TextField(blank=True)
    test_executable = models.CharField(max_length=250, blank=True)
    test_arguments = models.CharField(max_length=100, blank=True)
    suite_version = models.CharField(max_length=15, blank=True)
    igc_version = models.CharField(max_length=15, blank=True)
    neo_version = models.CharField(max_length=15, blank=True)
    dump = models.FileField(upload_to="dumps/", blank=True)

    def __str__(self):
        return (
            "CTS " + self.test_category + "/" + self.test_name
            + " (" + ("PASS" if self.passing else "FAIL") + ")"
            + " for job " + str(self.parent_job.pk)
        )

    class Meta:
        ordering = ["-date_added"]

    def sanitize(self):
        """
        Sanitizes the object's data before passing to a view.
        """
        self.parent_job.sanitize()
        self.standard_output = mark_safe(bleach.clean(self.standard_output))
        self.standard_error = mark_safe(bleach.clean(self.standard_error))
        self.test_executable = mark_safe(bleach.clean(self.test_executable))
        self.test_arguments = mark_safe(bleach.clean(self.test_arguments))
