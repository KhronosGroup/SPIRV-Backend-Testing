from rest_framework import serializers

from .models import CtsResult, Job, LitResult


class JobSerializer(serializers.ModelSerializer):
    revision_hash = serializers.CharField(source="revision.hash", read_only=True)

    class Meta:
        model = Job
        fields = (
            "pk",
            "status",
            "revision_hash",
            "run_lit_all",
            "run_cts_api",
            "run_cts_basic",
            "run_cts_atomics",
            "run_cts_buffers",
            "run_cts_commonfns",
            "run_cts_compiler",
            "run_cts_computeinfo",
            "run_cts_contractions",
            "run_cts_device_partition",
            "run_cts_events",
            "run_cts_geometrics",
            "run_cts_half",
            "run_cts_integer_ops",
            "run_cts_mem_host_flags",
            "run_cts_multiple_device_context",
            "run_cts_printf",
            "run_cts_profiling",
            "run_cts_relationals",
            "run_cts_select",
            "run_cts_thread_dimensions",
            "run_cts_vectors",
            "run_cts_c11_atomics",
            "run_cts_device_execution",
            "run_cts_non_uniform_work_group",
            "run_cts_generic_address_space",
            "run_cts_subgroups",
            "run_cts_workgroups",
            "run_cts_pipes",
            "run_cts_device_timer",
            "run_cts_spirv_new",
            "run_cts_math_brute_force",
            "run_cts_SVM",
            "run_cts_clCopyImage",
            "run_cts_clFillImage",
            "run_cts_clGetInfo",
            "run_cts_clReadWriteImage",
            "run_cts_kernel_image_methods",
            "run_cts_kernel_read_write",
            "run_cts_samplerlessReads",
        )


class JobDeserializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ("pk", "status", "status_details")


class LitResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = LitResult
        fields = ("test_path", "passing")


class CtsResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CtsResult
        fields = (
            "test_category",
            "test_name",
            "passing",
            "timedout",
            "start_time",
            "end_time",
            "standard_output",
            "standard_error",
            "test_executable",
            "test_arguments",
            "suite_version",
            "igc_version",
            "neo_version",
            "dump",
        )
