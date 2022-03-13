from progress import views

__author__ = 'antonior'

from django.conf.urls import url


urlpatterns = [
    url(r'^api/(?P<pipeline_id>[A-za-z0-9]+)/add_status', views.AddStatus.as_view()),
    url(r'^api/(?P<pipeline_id>[A-za-z0-9]+)', views.ProgressAPI.as_view(), name='progress_api'),
    url(r'^api', views.ProgressCreate.as_view()),
    url(r'^(?P<pipeline_id>[A-za-z0-9]+)', views.JobStatusDetail.as_view(), name='progress'),
    url(r'^', views.JobStatusDetail.as_view(), name='progress_status'),
]
