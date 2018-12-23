import os
import pandas
import plotly.graph_objs as go
import numpy
from plotly.offline import plot
import plotly.plotly as py
import plotly
import sys
import subprocess
#from .bench_plots_func import MEDIA_ROOT,BENCH_PLOTLY,PATH_TO_VENV, MEDIA_URL

# from bench_plots_func import Full_read_length_divs

print( "yo flipo")

def Full_read_length_divs(input_folder, path_to_venv=None, plotly_script=None, media_url=None, media_root=None, png=False):

    print("aqui entra")
    length_file = os.path.join(input_folder,"stat","readLengthFull.txt")
    out_path1 = os.path.join(input_folder,"stat","readLength_RC.png")
    out_path2 = os.path.join(input_folder,"stat","readLength_UR.png")

    #os.mkdir(os.path.join(input_folder, "stat", "1"))

    if (not os.path.exists(out_path1)) and (not png):
        print("aqui el if")
        call_list = [os.path.join(path_to_venv, "python"), plotly_script, "readLength", input_folder]
        with open(os.path.join(input_folder, "stat", "test.out"), "w") as test_f:
            test_f.write(" ".join(call_list))
        plotter = subprocess.Popen(call_list,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        with open(os.path.join(input_folder, "stat", "test2.out"), "w") as test_f:
            test_f.write(" ".join(call_list))


    #
    # if False:
    #     # os.system("touch " + os.path.join(input_folder, "stat", "2", "test.out"))
    #     # os.mkdir(os.path.join(input_folder,"stat","2"))
    #     #
    #     call = " ".join([os.path.join(path_to_venv,"python"), BENCH_PLOTLY ,"readLength", input_folder])
    #     with open(os.path.join(input_folder,"stat","test.out"), "w") as test_f:
    #         test_f.write(call)
    #     #os.system(" ".join([os.path.join(PATH_TO_VENV,"python"), BENCH_PLOTLY ,"readLength", input_folder]))
    #     #subprocess.call('source ' +os.path.join(PATH_TO_VENV,"activate") + ';' + call , shell=True)
    #     plotter = subprocess.Popen([os.path.join(PATH_TO_VENV,"python3.5"), BENCH_PLOTLY ,"readLength", input_folder],stdout=subprocess.PIPE,
    #                                  stderr=subprocess.PIPE)
    #     # [outStream, errStream] = plotter.communicate()
    #     # with open(os.path.join(input_folder,"stat","err.out"), "w") as test_f:
    #     #     test_f.write(str(outStream))
    #     #     test_f.write(str(errStream))
    #
    #     # subprocess.Popen([os.path.join(PATH_TO_VENV,"python3"), BENCH_PLOTLY ,"readLength", input_folder])
    #     # os.system("touch " + os.path.join(input_folder,"stat","2","test.out", "w"))
    # elif not os.path.exists(out_path1) :

    print("aqui sin if")

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
            ticksuffix='%',
            title='Percentage of reads')
    )
    fig = go.Figure(data=data, layout=layout)
    # py.image.save_as({'data': data}, 'your_image_filename.png')
    #plot(fig, filename=out_path1, show_link=False, auto_open=False)
    if png:
        plotly.io.write_image(fig, out_path1, format="png", width=None, height=None)
    else:
        div_obj1 = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)

    #div_obj1_b = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)

    data = [go.Bar(x=x,y=y2)]



    layout = go.Layout(
        margin=go.layout.Margin(
            l=50,
            r=50,
            b=100,
            t=100,
            pad=5
        ),

        title="Unique read length distribution ",
        autosize=False,
        font=dict(size=18),
        height=650,
        width=1150,
        xaxis=dict(
            # domain=[0.05, 1],
            automargin=True,
            title='Read length (nt)',
            tick0=0,
            dtick=1,
            # linecolor='black',
            # linewidth= 2,
            # mirror= True
        ),
        # yaxis: {
        #
        # range: [0, 1]
        yaxis=dict(
            ticksuffix='%',
            # type='log',
            title='Percentage of reads \n&nbsp;\n&nbsp;\n&nbsp;')
    )

    fig = go.Figure(data=data, layout=layout)

    if png:
        plotly.io.write_image(fig, out_path2, format="png", width=None, height=None)
    else:
        div_obj2 = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)
    #div_obj2 = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)
    # plot({'data': [{'y': [4, 2, 3, 4]}],
    #               'layout': {'title': 'Test Plot',
    #                          'font': dict(family='Comic Sans MS', size=16)}},
    #              auto_open=True, image='png', image_filename='plot_image',
    #              output_type='file', image_width=800, image_height=600,
    #              filename='temp-plot.html', validate=False)


    out_path1 = out_path1.replace(media_root,media_url)
    out_path2 = out_path2.replace(media_root,media_url)
    id1 = div_obj1.split("\"")[1]
    #id1_b = div_obj1_b.split("\"")[1]
    id2 = div_obj2.split("\"")[1]

    return [[div_obj1 ,out_path1, id1, "img_"+id1],[div_obj2, out_path2, id2, "img_"+id2]]
    # return [[div_obj2, out_path2, id2, "img_"+id2]]
    #return [[div_obj1 ,out_path1, id1, "img_"+id1],[div_obj1_b ,out_path1, id1_b, "img_"+id1_b]]



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



def main():
    print("pero esto que es")
    p_type = sys.argv[1]
    input_par = sys.argv[2]

    if p_type == "readLength":
        print("I see")
        Full_read_length_divs(input_par, png=True)

if __name__ == "__main__":
    main()

#stest_ml()

