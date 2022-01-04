import numpy
import math
import itertools
#import test

from plotly.offline import plot
import plotly.graph_objs as go
import pandas
import os.path
import plotly.plotly as py
import plotly.graph_objs as go
import plotly
import numpy as np

def makeSpeciesPlot(input_file):
    first_table = pandas.read_table(input_file, sep='\t')
    input_table = first_table.head(20)

    x_vals = []
    y_vals = []
    for index, row in input_table.iterrows():
        line = numpy.ndarray.flatten(row.values)
        x_vals.append(str(line[0].split(";")[0]))
        y_vals.append(int(line[2]))

    layout = go.Layout(
        autosize=True,

        margin=go.Margin(
            l=100,
            r=100,
            b=150,
            t=100,
            pad=4
        ),
        title="Top 20 species with the highest number of conserved sRNAs",
        xaxis=dict(
            tick0=0,
            dtick=1,
        ),
        yaxis=dict(
            title='Number of sRNAs')
    )
#    fig = go.Figure(data,layout=layout)
    fig = go.Figure([go.Bar(x=x_vals, y=y_vals,marker={'color': y_vals})],layout=layout)
    div_obj = plot(fig, show_link=False, auto_open=False, output_type = 'div')
    return div_obj


def makesrnasPlot(input_file):
    first_table = pandas.read_table(input_file, sep='\t')
    input_table = first_table.head(20)

    labels = input_table.columns[1:]
    x_vals = []
    y_vals = []
    data = []
    for index, row in input_table.iterrows():
        line = numpy.ndarray.flatten(row.values)
        x_vals.append(str(line[0].split(";")[0]))
        y_vals.append(int(line[2]))


    layout = go.Layout(
        autosize=True,

        margin=go.Margin(
            l=100,
            r=100,
            b=150,
            t=100,
            pad=4
        ),
        title="Top 20 conserved miRNAs",
        xaxis=dict(
            tick0=0,
            dtick=1,
        ),
        yaxis=dict(
            title='Number of species')
    )
#    fig = go.Figure(data,layout=layout)
    fig = go.Figure([go.Bar(x=x_vals, y=y_vals,marker={'color': y_vals})],layout=layout)
    div_obj = plot(fig, show_link=False, auto_open=False, output_type = 'div')
    return div_obj
