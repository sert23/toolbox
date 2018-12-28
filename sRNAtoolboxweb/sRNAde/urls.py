from sRNABench.views import result, test
from sRNAde.views import De, DeLaunch

__author__ = 'antonior'

from django.conf.urls import url


urlpatterns = [
    #url(r'^ncbiparser', views.NCBI.as_view(), name="ncbi"),
    url(r'result', result, name='srnade'),
    url(r'^$', De.as_view(), name="DE"),
    url(r'launch/(?P<pipeline_id>[A-za-z0-9]+)', DeLaunch.as_view()),
    url(r'launch/', DeLaunch.as_view(), name="DE_launch"),
    # url(r'^/*$', views.de),
    # url(r'run$', views.run, name='run_de'),

    url(r'test$', test),

]
