from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.new_upload, name='multi_new'),
    url(r'^download/[A-za-z0-9]+', views.multiDownload),
    url(r'^relaunch/[A-za-z0-9]+', views.RelaunchMulti),
    url(r'^relaunch/', views.RelaunchMulti, name='multi_relaunch'),
    url(r'^launch/[A-za-z0-9]+', views.MultiLaunchView.as_view()),
    url(r'^status/(?P<pipeline_id>[A-za-z0-9]+)', views.MultiStatusView.as_view()),
    url(r'^status/', views.MultiStatusView.as_view(), name='multi_status'),
    #url(r'^(pick/[A-za-z0-9]+)', views.PickSample.as_view()),
    # url(r'^/launch/[A-za-z0-9]+', views.MultiUploadView.as_view(), name='multi_launch'),
    #url(r'^(?P<query_id>[A-za-z0-9]+)', views.ProgressBarUploadView.as_view(),name='progress_bar_upload'),
    url(r'^[A-za-z0-9]+', views.MultiUploadView.as_view(),name='progress_bar_upload'),
    url(r'^launch/', views.DragAndDropUploadView.as_view(), name='multi_launch'),
    #url(r'^', views.MultiUploadView.as_view(), name='multi_start'),

    # url(r'^$', views.give_ID , name='multi_start'),
    # url(r'^$', views.ProgressBarUploadView.as_view() , name='multi_start'),
    #url(r'^clear/$', views.clear_database, name='clear_database'),
    # url(r'^$', Bench.as_view(), name="lolo"),
    ## url(r'^basic-upload/$', views.BasicUploadView.as_view(), name='basic_upload'),
    # url(r'^progress-bar-upload/$', views.ProgressBarUploadView.as_view(), name='progress_bar_upload'),
    #url(r'^drag-and-drop-upload/$', views.DragAndDropUploadView.as_view(), name='drag_and_drop_upload'),
]
