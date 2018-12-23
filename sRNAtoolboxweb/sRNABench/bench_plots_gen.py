import os
import pandas
import plotly.graph_objs as go
import numpy
from plotly.offline import plot
import plotly.plotly as py
import plotly
import sys

from bench_plots_func import Full_read_length_divs

# def Full_read_length_divs(input_folder):
#
#     length_file = os.path.join(input_folder,"stat","readLengthFull.txt")
#     out_path1 = os.path.join(input_folder,"stat","readLength_RC.png")
#     out_path2 = os.path.join(input_folder,"stat","readLength_UR.png")
#
#     input_table = pandas.read_table(length_file, sep='\t')
#     x = input_table["Read Length (nt)"].values
#     y1= input_table["Percentage_UR"].values
#     y2 = input_table["Percentage_RC"].values
#     data = [go.Bar(x=x, y=y1)]
#     layout = go.Layout(
#         autosize=True,
#         margin=go.layout.Margin(
#             l=50,
#             r=50,
#             b=150,
#             t=100,
#             pad=4
#         ),
#         title="Read length distribution ",
#         xaxis=dict(
#             title='Read length (nt)',
#             tick0=0,
#             dtick=1,
#         ),
#         yaxis=dict(
#             # type='log',
#             title='Percentage of reads (%)')
#     )
#     fig = go.Figure(data=data, layout=layout)
#     plotly.io.write_image(fig, out_path1, format="png",width=None, height=None)
#
#     data = [go.Bar(x=x,y=y2)]
#     layout = go.Layout(
#         autosize=True,
#         margin=go.layout.Margin(
#             l=50,
#             r=50,
#             b=150,
#             t=100,
#             pad=4
#         ),
#         title="Unique read length distribution ",
#         xaxis=dict(
#             title='Read length (nt)',
#             tick0=0,
#             dtick=1,
#         ),
#         yaxis=dict(
#             # type='log',
#             title='Percentage of reads (%)')
#     )
#     fig = go.Figure(data=data)
#     plotly.io.write_image(fig, out_path2, format="png", width=None, height=None)



# print(plotly.__version__)
#Full_read_length("C:/Users/Ernesto/Desktop/Colabo/Dani_platelets/")

p_type = sys.argv[1]
input_par = sys.argv[2]

if p_type == "readLength":
    Full_read_length_divs(input_par, png=True)

def stest_ml():
    from plotly.offline import init_notebook_mode, plot_mpl
    import matplotlib.pyplot as plt

    #init_notebook_mode()

    fig = plt.figure()
    x = [10, 15, 20, 25, 30]
    y = [100, 250, 200, 150, 300]
    plt.plot(x, y, "o")

    plot_mpl(fig)
    # If you want to to download an image of the figure as well
    plot_mpl(fig, image='png',image_filename='plot_image')

#stest_ml()

