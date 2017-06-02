__author__ = 'antonior'

from django.conf.urls import url
import views

urlpatterns = [
    url(r'^api/(?P<pipeline_id>[A-za-z0-9]+)', views.Progress.as_view()),
    url(r'^api', views.Progress.as_view()),
    url(r'^([A-za-z]+)', views.progress),
]
