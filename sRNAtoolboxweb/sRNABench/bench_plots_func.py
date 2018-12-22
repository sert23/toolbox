import os
import pandas
import plotly.graph_objs as go
import numpy
from plotly.offline import plot
import plotly.plotly as py
import plotly
import plotly.io as pio
from sRNAtoolboxweb.settings import MEDIA_ROOT,BENCH_PLOTLY,PATH_TO_VENV, MEDIA_URL
import subprocess


def Full_read_length_divs(input_folder, png=False):

    length_file = os.path.join(input_folder,"stat","readLengthFull.txt")
    out_path1 = os.path.join(input_folder,"stat","readLength_RC.png")
    out_path2 = os.path.join(input_folder,"stat","readLength_UR.png")

    #os.mkdir(os.path.join(input_folder, "stat", "1"))

    if False:
        # os.system("touch " + os.path.join(input_folder, "stat", "2", "test.out"))
        # os.mkdir(os.path.join(input_folder,"stat","2"))
        #
        call = " ".join([os.path.join(PATH_TO_VENV,"python"), BENCH_PLOTLY ,"readLength", input_folder])
        with open(os.path.join(input_folder,"stat","test.out"), "w") as test_f:
            test_f.write(call)
        #os.system(" ".join([os.path.join(PATH_TO_VENV,"python"), BENCH_PLOTLY ,"readLength", input_folder]))
        #subprocess.call('source ' +os.path.join(PATH_TO_VENV,"activate") + ';' + call , shell=True)
        plotter = subprocess.Popen([os.path.join(PATH_TO_VENV,"python3.5"), BENCH_PLOTLY ,"readLength", input_folder],stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
        # [outStream, errStream] = plotter.communicate()
        # with open(os.path.join(input_folder,"stat","err.out"), "w") as test_f:
        #     test_f.write(str(outStream))
        #     test_f.write(str(errStream))

        # subprocess.Popen([os.path.join(PATH_TO_VENV,"python3"), BENCH_PLOTLY ,"readLength", input_folder])
        # os.system("touch " + os.path.join(input_folder,"stat","2","test.out", "w"))
    # elif not os.path.exists(out_path1) :

    input_table = pandas.read_table(length_file, sep='\t')
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
        title="Read length distribution ",
        autosize=False,
        height=650,
        width=1150,
        xaxis=dict(
            title='Read length (nt)',
            tick0=0,
            dtick=1,
        ),
        yaxis=dict(
            # type='log',
            title='Percentage of reads')
    )
    fig = go.Figure(data=data, layout=layout)
    # py.image.save_as({'data': data}, 'your_image_filename.png')
    #plot(fig, filename=out_path1, show_link=False, auto_open=False)
    div_obj1 = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)


    data = [go.Bar(x=x,y=y2)]

    layout = go.Layout(
        margin=go.layout.Margin(
            l=50,
            r=50,
            b=100,
            t=100,
            pad=4
        ),
        title="Unique read length distribution ",
        autosize=False,
        height=650,
        width=1150,
        xaxis=dict(
            title='Read length (nt)',
            tick0=0,
            dtick=1,
        ),
        yaxis=dict(
            # type='log',
            title='Percentage of reads')
    )

    fig = go.Figure(data=data)

    div_obj2 = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)
    # plot({'data': [{'y': [4, 2, 3, 4]}],
    #               'layout': {'title': 'Test Plot',
    #                          'font': dict(family='Comic Sans MS', size=16)}},
    #              auto_open=True, image='png', image_filename='plot_image',
    #              output_type='file', image_width=800, image_height=600,
    #              filename='temp-plot.html', validate=False)

    out_path1 = out_path1.replace(MEDIA_ROOT,MEDIA_URL)
    out_path2 = out_path2.replace(MEDIA_ROOT,MEDIA_URL)
    id1 = div_obj1.split("\"")[1]
    id2 = div_obj2.split("\"")[1]

    return [[div_obj1 ,out_path1, id1, "img_"+id1],[div_obj2, out_path2, id2, "img_"+id2]]

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

