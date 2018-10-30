from photos.views import ProgressBarUploadView

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.give_ID , name='multi_start'),
    url(r'^[A-za-z0-9]+', ProgressBarUploadView.as_view(), name='progress_bar_upload'),
    # url(r'^$', views.ProgressBarUploadView.as_view() , name='multi_start'),
    url(r'^clear/$', views.clear_database, name='clear_database'),
    # url(r'^basic-upload/$', views.BasicUploadView.as_view(), name='basic_upload'),
    url(r'^progress-bar-upload/$', views.ProgressBarUploadView.as_view(), name='progress_bar_upload'),
    url(r'^drag-and-drop-upload/$', views.DragAndDropUploadView.as_view(), name='drag_and_drop_upload'),
]
