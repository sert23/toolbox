#from sRNABench.views import Bench

__author__ = 'antonior'

from django.conf.urls import url
from . import views

urlpatterns = [
    #url(r'results', views.result_new, name='srnabench'),
    #url(r'results', views.result),
    #url(r'table/(.+)/(.+)/(.+)*', views.render_table, name='table_bench'),
    #url(r'align/(.+)/(.+)/(.+)', views.show_align, name='show_align'),
    # url(r'run$', views.run, name='run_bench'),
    url(r'^$', views.NewUpload.as_view()),
    url(r'^annotate/', views.Launch.as_view(), name="annotate"),
    url(r'^relaunch', views.ReLaunch.as_view(), name="newbench_relaunch"),
    url(r'^matrix_selector', views.ajax_matrix_selectors, name="ajax_matrix_selector"),
    url(r'^matrix_generator', views.matrix_generator, name="matrix_generator"),
    url(r'^contamination', views.contaminaBench.as_view(), name="contamination"),
    url(r'^ajax_read_length_graph', views.ajax_read_length, name="ajax_read_length_graph"),
    # url(r'^launch/[A-za-z0-9]+', views.NewUpload.as_view()),
    #url(r'test$', views.test),
]
