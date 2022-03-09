from sRNABench.views import  test
from sRNAde.views import De, DeLaunch, result, De_method_view,DeFromMulti,SeqVar_view, DeFromMultiAnnot

__author__ = 'antonior'

from django.conf.urls import url


urlpatterns = [
    #url(r'^ncbiparser', views.NCBI.as_view(), name="ncbi"),


    # url(r'de/(?P<pipeline_id>[A-za-z0-9]+)', De_method_view.as_view()),
    url(r'multi/', DeFromMulti.as_view(), name="DE_multi"),
    url(r'multi/(?P<pipeline_id>[A-za-z0-9]+)', DeFromMulti.as_view()),
    url(r'seqvar/(?P<pipeline_id>[A-za-z0-9]+)', SeqVar_view.as_view()),
    url(r'seqvar/', SeqVar_view.as_view(), name="DE_seqvar"),
    url(r'de/[A-za-z0-9]+/(?P<pipeline_id>[A-za-z0-9]+)', De_method_view.as_view()),
    url(r'de/', De_method_view.as_view(), name='de_method'),
    url(r'result', result, name='srnade'),
    url(r'^$', De.as_view(), name="DE"),
    url(r'launch/(?P<pipeline_id>[A-za-z0-9]+)', DeLaunch.as_view()),
    url(r'launch/', DeLaunch.as_view(), name="DE_launch"),
    url(r'fromannot/', DeFromMultiAnnot.as_view(), name="launch_annot"),
    url(r'fromannot/(?P<pipeline_id>[A-za-z0-9]+)', DeFromMultiAnnot.as_view()),
    # url(r'^/*$', views.de),
    # url(r'run$', views.run, name='run_de'),

    url(r'test$', test),

]
