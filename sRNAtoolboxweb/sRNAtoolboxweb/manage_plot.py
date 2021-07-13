
import os
import pandas
import plotly.graph_objs as go
import numpy
from plotly.offline import plot
import plotly.plotly as py
import plotly
import sys
import subprocess
from datetime import timedelta
from django.utils import timezone
from progress.models import JobStatus
# from django.db.models.lookups import MonthTransform as Month, YearTransform as Year
from django.db.models import Count


def list_counter(input_list):
    uniques = set(input_list)
    res_dict={}
    for u in uniques:
        res_dict[u] = input_list.count(u)
    return res_dict

###

# def month_ranking():
#     JobStatus.objects.annotate(
#         year=Year('date'),
#         month=Month('date'),
#     ).values('year', 'month').annotate(count=Count('pk'))
#

def stacked_bars_state():

    last_month = timezone.now().date() - timedelta(days=30)
    last_week = timezone.now().date() - timedelta(days=7)
    last_day = timezone.now().date() - timedelta(days=1)

    queries_month = JobStatus.objects.filter(start_time__range=(last_month, timezone.now()))
    queries_week = JobStatus.objects.filter(start_time__range=(last_week, timezone.now()))
    queries_day = JobStatus.objects.filter(start_time__range=(last_day, timezone.now()))
    queries_all = JobStatus.objects.all()

    times_dict = {}

    times_dict["last month"] = list(queries_month.values_list("job_status", flat=True))
    times_dict["last week"] = list(queries_week.values_list("job_status", flat=True))
    times_dict["last 24h"] = list(queries_day.values_list("job_status", flat=True))
    times_dict["always"] = list(queries_all.values_list("job_status", flat=True))

    tags_set = sorted(list(set(times_dict["always"])))

    data = []
    times = ["last 24h", "last week", "last month", "always"]
    for tag in tags_set:
        x = times
        y = []
        for t in times:
            curr_list = times_dict[t]
            y.append(curr_list.count(tag))
        trace = go.Bar(x=x,
                       y=y,
                       name=tag)
        data.append(trace)

    layout = go.Layout(
        barmode='relative'
        # barmode='stack'
    )
    fig = go.Figure(data=data, layout=layout)
    div_obj1 = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=True)
    return div_obj1

def stacked_bars_state_percentage():

    last_month = timezone.now().date() - timedelta(days=30)
    last_week = timezone.now().date() - timedelta(days=7)
    last_day = timezone.now().date() - timedelta(days=1)

    queries_month = JobStatus.objects.filter(start_time__range=(last_month, timezone.now()))
    queries_week = JobStatus.objects.filter(start_time__range=(last_week, timezone.now()))
    queries_day = JobStatus.objects.filter(start_time__range=(last_day, timezone.now()))
    queries_all = JobStatus.objects.all()

    times_dict = {}

    times_dict["last month"] = list(queries_month.values_list("job_status", flat=True))
    times_dict["last week"] = list(queries_week.values_list("job_status", flat=True))
    times_dict["last 24h"] = list(queries_day.values_list("job_status", flat=True))
    times_dict["always"] = list(queries_all.values_list("job_status", flat=True))

    tags_set = sorted(list(set(times_dict["always"])))

    data = []
    times = ["last 24h", "last week", "last month", "always"]
    for tag in tags_set:
        x = times
        y = []
        yl = []
        for t in times:
            curr_list = times_dict[t]
            y.append(curr_list.count(tag)/float(len(curr_list)))
            yl.append(curr_list.count(tag))

        trace = go.Bar(x=x,
                       y= y,
                       text = yl,
                       name=tag)
        data.append(trace)

    layout = go.Layout(
        barmode='relative'
        # barmode='stack'
    )
    fig = go.Figure(data=data, layout=layout)
    div_obj1 = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=True)
    return div_obj1

def job_type():
    last_month = timezone.now().date() - timedelta(days=30)
    last_week = timezone.now().date() - timedelta(days=7)
    last_day = timezone.now().date() - timedelta(days=1)

    queries_month = JobStatus.objects.filter(start_time__range=(last_month, timezone.now()))
    queries_week = JobStatus.objects.filter(start_time__range=(last_week, timezone.now()))
    queries_day = JobStatus.objects.filter(start_time__range=(last_day, timezone.now()))
    queries_all = JobStatus.objects.all()

    times_dict = {}

    times_dict["last month"] = list(queries_month.values_list("pipeline_type", flat=True))
    times_dict["last week"] = list(queries_week.values_list("pipeline_type", flat=True))
    times_dict["last 24h"] = list(queries_day.values_list("pipeline_type", flat=True))
    times_dict["always"] = list(queries_all.values_list("pipeline_type", flat=True))

    tags_set = sorted(list(set(times_dict["always"])))

    data = []
    times = ["last 24h", "last week", "last month", "always"]
    for tag in tags_set:
        x = times
        y = []
        yl = []
        for t in times:
            curr_list = times_dict[t]
            y.append(curr_list.count(tag) / float(len(curr_list)))
            yl.append(curr_list.count(tag))

        trace = go.Bar(x=x,
                       y=y,
                       text=yl,
                       name=tag)
        data.append(trace)

    layout = go.Layout(
        barmode='relative'
        # barmode='stack'
    )
    fig = go.Figure(data=data, layout=layout)
    div_obj1 = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=True)
    return div_obj1
#
# def number_finished():
