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


def Full_read_length_divs(input_folder, path_to_venv=None, plotly_script=None, media_url=None, media_root=None, png=False):

    length_file = os.path.join(input_folder,"stat","readLengthFull.txt")
    out_path1 = os.path.join(input_folder,"stat","readLength_RC.png")
    out_path2 = os.path.join(input_folder,"stat","readLength_UR.png")

    #os.mkdir(os.path.join(input_folder, "stat", "1"))

    if (not os.path.exists(out_path1)) and (not png):

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

        title="Read length distribution ",
        autosize=False,
        font=dict(size=18),
        height=650,
        width=1150,
        xaxis=dict(
            # domain=[0.05, 1],
            automargin=True,
            title='Read length (nt)',
            tick0=0,
            dtick=2,
            # linecolor='black',
            # linewidth= 2,
            # mirror= True
        ),
        # yaxis: {
        #
        # range: [0, 1]
        yaxis=dict(
            automargin=True,
            ticksuffix='%',
            tickprefix="   ",

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



# print(plotly.__version__)
#Full_read_length("C:/Users/Ernesto/Desktop/Colabo/Dani_platelets/")

def Read_len_type(input_folder, path_to_venv=None, plotly_script=None, media_url=None, media_root=None,
                          png=False):
    length_file = os.path.join(input_folder, "stat", "rnaComposition_readLength_sensePref.txt")
    out_path = os.path.join(input_folder, "stat", "rnaComposition_readLength.png")

    # if False:
    if (not os.path.exists(out_path)) and (not png):
        call_list = [os.path.join(path_to_venv, "python"), plotly_script, "lenType", input_folder]
        with open(os.path.join(input_folder, "stat", "testP.out"), "w") as test_f:
            test_f.write(" ".join(call_list))
        plotter = subprocess.Popen(call_list,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        with open(os.path.join(input_folder, "stat", "test2.out"), "w") as test_f:
            test_f.write(" ".join(call_list))

    input_table = pandas.read_table(length_file, sep='\t')
    lengths = input_table.iloc[:,0].values
    names = list(input_table.columns.values)
    #print(x)

    print(input_table.shape[1])
    data = []
    for i in range(input_table.shape[1]-1):
        print(input_table.iloc[:,i+1].values)
        print(names[i + 1])

        trace = go.Bar(
            x = lengths,
            y = input_table.iloc[:,i+1].values,
            name = names[i+1],
            marker =dict(
                colorscale="Viridis"
            )
        )
        data.append(trace)

    layout = go.Layout(
        margin=go.layout.Margin(
            l=50,
            r=50,
            b=100,
            t=100,
            pad=4
        ),

        barmode="stack",
        title="Read length distribution ",
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
    # py.image.save_as({'data': data}, 'your_image_filename.png')
    # plot(fig, filename=out_path1, show_link=False, auto_open=False)
    if png:
        plotly.io.write_image(fig, out_path, format="png", width=None, height=None)
        # plotly.io.write_image(fig, out_path, format="png", width=None, height=None)
    else:
        div_obj1 = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)

        out_path = out_path.replace(media_root, media_url)
        id1 = div_obj1.split("\"")[1]
        # id1_b = div_obj1_b.split("\"")[1]

        return [[div_obj1, out_path, id1, "img_" + id1]]



def Mapping_stat_plot(input_folder, path_to_venv=None, plotly_script=None, media_url=None, media_root=None,
                          png=False):
    length_file = os.path.join(input_folder, "stat", "mappingStat_sensePref.txt")
    out_path = os.path.join(input_folder, "stat", "mappingStat_sensePref.png")

    # if False:
    if (not os.path.exists(out_path)) and (not png):
        call_list = [os.path.join(path_to_venv, "python"), plotly_script, "mapStat", input_folder]
        with open(os.path.join(input_folder, "stat", "testP.out"), "w") as test_f:
            test_f.write(" ".join(call_list))
        plotter = subprocess.Popen(call_list,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        with open(os.path.join(input_folder, "stat", "test2.out"), "w") as test_f:
            test_f.write(" ".join(call_list))

    input_table = pandas.read_table(length_file, sep='\t')
    x = input_table["name"].values
    y = input_table["RCperc"].values
    trace = go.Bar(
        x=x,
        y=y,
        marker=dict(
            color=['rgb(31, 119, 180)', 'rgb(255, 127, 14)',
                         'rgb(44, 160, 44)', 'rgb(214, 39, 40)',
                         'rgb(148, 103, 189)', 'rgb(140, 86, 75)',
                         'rgb(227, 119, 194)', 'rgb(127, 127, 127)',
                         'rgb(188, 189, 34)', 'rgb(23, 190, 207)'],
            colorscale="Viridis"
        ),

        # marker=dict(
        #
        # )
    )
    data = [trace]
    layout = go.Layout(
        margin=go.layout.Margin(
            l=50,
            r=50,
            b=100,
            t=100,
            pad=4
        ),

        # barmode="stack",
        title="RNA distribution",
        font=dict(size=18),
        autosize=False,
        height=650,
        width=1150,
        xaxis=dict(
            automargin=True,
            title=' ',
            tick0=0,
            # dtick=2,
        ),
        yaxis=dict(
            # type='log',
            automargin=True,
            ticksuffix='%',
            tickprefix="   ",
            title='Percentage of reads')
    )

    fig = go.Figure(data=data, layout=layout)
    if png:
        plotly.io.write_image(fig, out_path, format="png", width=None, height=None)
        # plotly.io.write_image(fig, out_path, format="png", width=None, height=None)
    else:
        div_obj1 = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)

        out_path = out_path.replace(media_root, media_url)
        id1 = div_obj1.split("\"")[1]
        # id1_b = div_obj1_b.split("\"")[1]

        return [[div_obj1, out_path, id1, "img_" + id1]]

def top_miRs_plot(input_file, title=".", path_to_venv=None, plotly_script=None, media_url=None, media_root=None,
                          png=False):

    no_ext = ".".join(input_file.split(".")[:-1])
    out_path = no_ext + ".png"
    # if False:
    if (not os.path.exists(out_path)) and (not png):
        call_list = [os.path.join(path_to_venv, "python"), plotly_script, "topMir", input_file, title]
        with open(no_ext + "testP.out", "w") as test_f:
            test_f.write(" ".join(call_list))
        plotter = subprocess.Popen(call_list,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
    input_table = pandas.read_table(input_file, sep='\t')
    ordered_table = input_table.sort_values(by=["RPM (total)"], ascending=False)
    clean_table = ordered_table.drop_duplicates(subset=["name"])
    x=clean_table["name"].values[:10]
    y=clean_table["RPM (total)"].values[:10]

    trace = go.Bar(
        x=x,
        y=y,
        marker=dict(
            color=['rgb(31, 119, 180)']*len(x),
            colorscale="Viridis"
        ))
    data = [trace]
    layout = go.Layout(
        margin=go.layout.Margin(
            l=50,
            r=50,
            b=100,
            t=100,
            pad=4
        ),
        # barmode="stack",
        title=title,
        font=dict(size=18),
        autosize=False,
        height=650,
        width=1150,
        xaxis=dict(
            automargin=True,
            # title='Read length (nt)',
            tick0=0,
            # dtick=2,
        ),
        yaxis=dict(
            # type='log',
            automargin=True,
            ticksuffix=' RPM',
            tickprefix="    ",
            title='Reads Per Million (RPM)')
    )

    fig = go.Figure(data=data, layout=layout)

    if png:
        plotly.io.write_image(fig, out_path, format="png", width=None, height=None)
        # plotly.io.write_image(fig, out_path, format="png", width=None, height=None)
    else:
        div_obj1 = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)

        out_path = out_path.replace(media_root, media_url)
        id1 = div_obj1.split("\"")[1]
        # id1_b = div_obj1_b.split("\"")[1]

        return [[div_obj1, out_path, id1, "img_" + id1]]

    # plot(fig, show_link=False, auto_open=True, output_type='div', include_plotlyjs=False)


#top_miRs_plot("C:/Users/Ernesto/Desktop/Colabo/Dani_platelets/mature_sense.grouped", title="Top 10 expressed miRNAs")



def main():
    p_type = sys.argv[1]
    input_par = sys.argv[2]
    if len (sys.argv) > 3:
        input_par2 = sys.argv[3]

    if p_type == "readLength":
        Full_read_length_divs(input_par, png=True)
    if p_type == "lenType":
        Read_len_type(input_par, png=True)
    if p_type == "mapStat":
        Mapping_stat_plot(input_par, png=True)
    if p_type == "topMir":
        top_miRs_plot(input_par, title=input_par2, png=True)

if __name__ == "__main__":
    main()

#stest_ml()

