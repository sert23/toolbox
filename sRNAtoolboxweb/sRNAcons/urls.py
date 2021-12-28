from . import views
from django.conf.urls import url


urlpatterns = [
    url(r'result', views.result, name="srnacons"),
    url(r'^$', views.sRNAcons.as_view(), name="SRNACONS")
]