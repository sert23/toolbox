__author__ = 'antonior'

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'results', views.result_new),
    #url(r'results', views.result),
    url(r'table/(.+)/(.+)/(.+)*', views.render_table),
    url(r'align/(.+)/(.+)/(.+)', views.show_align),
    url(r'run$', views.run, name='run_bench'),
    url(r'^/*$', views.input),
    url(r'test$', views.test),
]
