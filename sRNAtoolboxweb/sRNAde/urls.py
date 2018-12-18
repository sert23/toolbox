__author__ = 'antonior'

from django.conf.urls import url
from . import views

urlpatterns = [
    #url(r'^ncbiparser', views.NCBI.as_view(), name="ncbi"),
    url(r'result', views.result, name='srnade'),
    url(r'^$', views.De.as_view(), name="DE"),
    url(r'launch/(?P<pipeline_id>[A-za-z0-9]+)', views.DeLaunch.as_view()),
    url(r'launch/', views.DeLaunch.as_view(), name="DE_launch"),
    # url(r'^/*$', views.de),
    # url(r'run$', views.run, name='run_de'),

    url(r'test$', views.test),

]
