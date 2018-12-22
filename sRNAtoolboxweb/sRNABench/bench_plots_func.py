import os
import pandas
import plotly.graph_objs as go
import numpy
from plotly.offline import plot
import plotly.plotly as py
import plotly
import plotly.io as pio
from sRNAtoolboxweb.settings import MEDIA_ROOT,BENCH_PLOTLY,PATH_TO_VENV
import subprocess


def Full_read_length_divs(input_folder, generate=True):

    length_file = os.path.join(input_folder,"stat","readLengthFull.txt")
    out_path1 = os.path.join(input_folder,"stat","readLength_RC.png")
    out_path2 = os.path.join(input_folder,"stat","readLength_UR.png")

    #os.mkdir(os.path.join(input_folder, "stat", "1"))

    if not os.path.exists(out_path1):
        # os.system("touch " + os.path.join(input_folder, "stat", "2", "test.out"))
        # os.mkdir(os.path.join(input_folder,"stat","2"))
        #
        with open(os.path.join(input_folder,"stat","test.out"), "w") as test_f:
            test_f.write(" ".join([os.path.join(PATH_TO_VENV,"python"), BENCH_PLOTLY ,"readLength", input_folder]))
        os.system(" ".join([os.path.join(PATH_TO_VENV,"python"), BENCH_PLOTLY ,"readLength", input_folder]))
        subprocess.Popen([os.path.join(PATH_TO_VENV,"python"), BENCH_PLOTLY ,"readLength", input_folder])
        # os.system("touch " + os.path.join(input_folder,"stat","2","test.out", "w"))


    input_table = pandas.read_table(length_file, sep='\t')
    x = input_table["Read Length (nt)"].values
    y1= input_table["Percentage_UR"].values
    y2 = input_table["Percentage_RC"].values
    data = [go.Bar(x=x, y=y1)]
    layout = go.Layout(
        autosize=True,
        margin=go.Margin(
            l=50,
            r=50,
            b=150,
            t=100,
            pad=4
        ),
        title="Read length distribution ",
        xaxis=dict(
            title='Read length (nt)',
            # tick0=0,
            # dtick=1,
        ),
        yaxis=dict(
            # type='log',
            title='Percentage of reads')
    )
    fig = go.Figure(data=data, layout=layout)
    # py.image.save_as({'data': data}, 'your_image_filename.png')
    #plot(fig, filename=out_path1, show_link=False, auto_open=False)
    div_obj1 = plot(fig, show_link=False, auto_open=False, output_type='div')


    data = [go.Bar(x=x,y=y2)]
    layout = go.Layout(
        autosize=True,
        margin=go.Margin(
            l=50,
            r=50,
            b=150,
            t=100,
            pad=4
        ),
        title="Unique read length distribution ",
        xaxis=dict(
            title='Read length (nt)',
            # tick0=0,
            # dtick=1,
        ),
        yaxis=dict(
            # type='log',
            title='Percentage of reads')
    )
    fig = go.Figure(data=data)

    div_obj2 = plot(fig, show_link=False, auto_open=False, output_type='div')
    plot({'data': [{'y': [4, 2, 3, 4]}],
                  'layout': {'title': 'Test Plot',
                             'font': dict(family='Comic Sans MS', size=16)}},
                 auto_open=True, image='png', image_filename='plot_image',
                 output_type='file', image_width=800, image_height=600,
                 filename='temp-plot.html', validate=False)

    # return div_obj1 ,div_obj2, out_path1, out_path2

#     plotly.io.write_image(fig, file, format=None,
#                           scale=None, width=None, height=None)
#     layout = go.Layout(
#         autosize=True,
#         margin=go.Margin(
#             l=50,
#             r=50,
#             b=150,
#             t=100,
#             pad=4
#         ),
#         title="Read length statistics ",
#         xaxis=dict(
#             title='Read length',
#             tick0=0,
#             dtick=1,
#         ),
#         yaxis=dict(
#             title='Percentage of reads (%)')
#     )
#
#
#
# print(plotly.__version__)
#Full_read_length("C:/Users/Ernesto/Desktop/Colabo/Dani_platelets/")

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

