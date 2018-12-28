"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import os

from django.test import TestCase, Client
from django.urls import reverse

from progress.models import JobStatus


class SimpleTest(TestCase):
    def setUp(self):
        self.js = JobStatus.objects.create(
            job_name='name',
            pipeline_key='key',
            job_status='finished',
            modules_files='f',
            pipeline_type='f',
            outdir=os.path.join(os.path.dirname(__file__), 'test_resources'),
            command_line='f',
            all_files=''
        )

    def test_novel_table(self):
        client = Client()
        response = client.get(reverse('table_bench', args=['novel', self.js.pipeline_key]))
        self.assertEqual(response.status_code, 200)


