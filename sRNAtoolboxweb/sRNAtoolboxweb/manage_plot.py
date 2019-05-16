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


def list_counter(input_list):
    uniques = set(input_list)
    res_dict={}
    for u in uniques:
        res_dict[u] = input_list.count(u)
    return res_dict

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

    old_set = set()
    for k in times_dict.keys():
        old_set.update(times_dict[k])

    return old_set





    #input_table = pandas.read_table(length_file, sep='\t')
    x = input_table["Read Length (nt)"].values
    y1= input_table["Percentage_UR"].values
    y2 = input_table["Percentage_RC"].values
    data = [go.Bar(x=x, y=y1)]
    layout = go.Layout(
        margin=go.layout.Margin(
            l=50,
            r=50,
            b=100,
            t=100,
            pad=4
        ),
        title="Unique read length distribution ",
        font=dict(size=18),
        autosize=False,
        height=650,
        width=1150,
        xaxis=dict(
            automargin=True,
            title='Read length (nt)',
            tick0=0,
            dtick=2,
        ),
        yaxis=dict(
            # type='log',
            automargin=True,
            ticksuffix='%',
            tickprefix="   ",
            title='Percentage of reads')
    )
    fig = go.Figure(data=data, layout=layout)