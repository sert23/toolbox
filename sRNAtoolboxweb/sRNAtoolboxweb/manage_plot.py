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


def stacked_bars_state_percentage():
    last_month = timezone.now().date() - timedelta(days=30)
    last_week = timezone.now().date() - timedelta(days=7)
    last_day = timezone.now().date() - timedelta(days=1)

    queries_month = JobStatus.objects.filter(start_time__range=(last_month, timezone.now()))
    estring = queries_month.values_list("job_status")
    return(list(estring))
    print(queries_month)
    print(len(queries_month))
    exit()


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