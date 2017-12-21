from django.contrib import admin

from .models import JobStatus


class JobStatusAdmin(admin.ModelAdmin):
     list_display = ('pipeline_type', 'pipeline_key', 'start_time', 'finish_time', 'job_status', 'outdir')

admin.site.register(JobStatus, JobStatusAdmin)