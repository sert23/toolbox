from django.db import models
import datetime
import django.utils

class JobStatus (models.Model):
    job_name = models.CharField(max_length=100)
    # tool = models.CharField(max_length=100)
    pipeline_key = models.CharField(max_length=100)
    #job_status_progress = ListField(models.CharField(max_length=400))
    job_status = models.CharField(max_length=100)
    start_time = models.DateTimeField(default=django.utils.timezone.now)
    finish_time = models.DateTimeField(null=True, blank=True)
    all_files = models.CharField(max_length=1000, null=True)
    modules_files = models.CharField(max_length=1000)
    pipeline_type = models.CharField(max_length=100)
    heatmaps = models.CharField(max_length=1000, null=True)
    xls_files = models.CharField(max_length=1000, null=True)
    zip_file = models.CharField(max_length=1000, null=True)
    stats_file = models.CharField(max_length=1000, null=True)
    blast_file = models.CharField(max_length=1000, null=True)
    species_file = models.CharField(max_length=1000, null=True)
    tax_file = models.CharField(max_length=1000, null=True)
    tax_svg = models.CharField(max_length=1000, null=True)
    species_svg = models.CharField(max_length=1000, null=True)
    bed_files = models.CharField(max_length=1000, null=True)
    ts_file = models.CharField(max_length=1000, null=True)
    pita_file = models.CharField(max_length=1000, null=True)
    miranda_file = models.CharField(max_length=1000, null=True)
    consensus_file = models.CharField(max_length=1000, null=True)
    info_file = models.CharField(max_length=1000, null=True)
    micro_file = models.CharField(max_length=1000, null=True)
    outdir = models.CharField(max_length=1000)
    parameters = models.CharField(max_length=1000, null=True)
    command_line = models.CharField(max_length=1000)
    java_commad_line = models.CharField(max_length=1000, null=True)

    def __str__(self):
        return self.job_status

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.pk:
            super(JobStatus, self).save()
        else:
            super(JobStatus, self).save()
            self.status.create(status_progress='not_launched')

class Status(models.Model):

    status_progress=models.CharField(max_length=1000)
    JobStatus = models.ForeignKey(
        JobStatus,
        on_delete=models.CASCADE,
        related_name='status'
    )

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super(Status, self).save()
        self.JobStatus.job_status = self.status_progress
