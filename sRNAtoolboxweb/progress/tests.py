"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from datetime import datetime

from django.test import TestCase

from progress.models import JobStatus


class SimpleTest(TestCase):
    def test_create_delete_update(self):
        JobStatus.objects.create(job_name='lele',
                                 pipeline_key="rrr", job_status="jj", start_time=datetime.now(),
                                 finish_time=datetime.now(), all_files="ll", modules_files="mm",
                                 pipeline_type="cool", heatmaps="cold_treasure", xls_files="Micros",
                                 zip_file=".zip", stats_file="sts", blast_file="blst", species_file="hg",
                                 outdir="output", parameters="x,y", command_line="bash_lime",
                                 java_commad_line="jar")

        self.assertEqual(len(JobStatus.objects.all()), 1)
        self.assertEqual(len(JobStatus.objects.first().status.all()), 1)
