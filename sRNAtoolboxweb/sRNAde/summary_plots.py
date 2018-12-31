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

def makeGenomePlot(input_file, output_file):
    first_table = pandas.read_table(input_file, sep='\t')
    input_table = first_table.head(10)
    data = []

    labels = input_table.columns[1:]

    for index, row in input_table.iterrows():
        line = numpy.ndarray.flatten(row.values)
        trace = go.Box(
            y=line[1:-1],
            name=line[0],
            text=labels
        )
        data.append(trace)
    layout = go.Layout(
        autosize=True,

        margin=go.Margin(
            l=50,
            r=50,
            b=150,
            t=100,
            pad=4
        ),
        title="RNA types distribution",
        xaxis=dict(
            # title='Nulceotide added',
            tick0=0,
            dtick=1,
        ),
        yaxis=dict(
            title='Percentage of reads (%)')
    )
    fig = go.Figure(data=data, layout=layout)
    div_obj = plot(fig, show_link=False, auto_open=False, output_type = 'div')
    return div_obj

def makeTop20(input_file, output_file):
    first_table = pandas.read_table(input_file, sep='\t')
    input_table = first_table.head(20)
    data = []

    # adding 1
    # numeric_cols = list(input_table.columns)
    # numeric_cols.remove("name")
    # input_table[numeric_cols] += 1

    labels = input_table.columns[1:]

    for index, row in input_table.iterrows():
        line = numpy.ndarray.flatten(row.values)
        trace = go.Box(
            y=line[1:-1]+1,
            name=line[0],
            text=labels
        )
        data.append(trace)



    layout = go.Layout(
        autosize=True,
        margin=go.Margin(
            l=50,
            r=50,
            b=150,
            t=100,
            pad=4
        ),
        title="20 most abundant microRNAs",
        xaxis=dict(
            # title='Nulceotide added',
            tick0=0,
            dtick=1,
        ),
        yaxis=dict(
            type='log',
            title='RPM+1')
    )
    fig = go.Figure(data=data, layout=layout)
    div_obj = plot(fig, show_link=False, auto_open=False, output_type = 'div')
    return div_obj

def makePie10(input_file):
    first_table = pandas.read_table(input_file, sep='\t')
    input_table = first_table.head(10)
    others = first_table.tail(first_table.shape[0]-10)
    others_val = sum(others[["sum"]].values)
    print(others_val)
    labels =list(numpy.ndarray.flatten(input_table[["name"]].values)) + ["Others"]
    # first_table = first_table.drop("sum", axis=1)
    averagecol = first_table.mean(axis=1)
    # total = sum(averagecol)
    # print(first_table.shape)
    # print(averagecol[0])
    # print(len(averagecol))
    # print(total)
    data = []
    values = (list(numpy.ndarray.flatten(input_table[["sum"]].values)))+ list(numpy.ndarray.flatten(others_val))
    print(labels)
    print(values)
    trace = go.Pie(labels=labels, values=values)
    data.append(trace)
    layout = go.Layout(
        autosize=True,
        margin=go.Margin(
            l=50,
            r=50,
            b=150,
            t=100,
            pad=4
        ),
        title="10 most abundant microRNAs",
        # xaxis=dict(
        #     # title='Nulceotide added',
        #     tick0=0,
        #     dtick=1,
        # ),
        # yaxis=dict(
        #     #type='log',
        #     title='RPM')
    )
    fig = go.Figure(data=data, layout=layout)
    div_obj = plot(fig, show_link=False, auto_open=False, output_type='div')
    return div_obj

#makePie10("C:/Users/Ernesto/PycharmProjects/liqDB/gentelella/data_folder/studies/SRP062974/miRNA_RPMadjLib_sort.txt")

def makeSpeciesPlot(input_file):
    first_table = pandas.read_table(input_file, sep='\t')
    input_table = first_table.head(10)
    data = []

    labels = input_table.columns[1:]

    for index, row in input_table.iterrows():
        line = numpy.ndarray.flatten(row.values)
        trace = go.Box(
            y=line[1:-1],
            name=line[0],
            text=labels
        )
        data.append(trace)
    layout = go.Layout(
        autosize=True,
        margin=go.Margin(
            l=50,
            r=50,
            b=150,
            t=100,
            pad=4
        ),
        title="Genomes distribution",
        xaxis=dict(
            # title='Nulceotide added',
            tick0=0,
            dtick=1,
        ),
        yaxis=dict(
            title='Percentage of reads (%)')
    )
    fig = go.Figure(data=data, layout=layout)
    div_obj = plot(fig, show_link=False, auto_open=False, output_type='div')
    return div_obj


#makeGenomePlot("C:/Users/Ernesto/PycharmProjects/liqDB/gentelella/data_folder/studies/SRP062974/RCperc_genome.txt","")

def makeTop20CV(input_file):
    first_table = pandas.read_table(input_file, sep='\t')
    ordered = first_table.sort_values(by="CV", axis=0, ascending=False)
    clean = ordered.drop(["stddev",	"CV", "mean"],axis=1)
    top20 = clean.head(20)
    labels = top20.columns[1:]

    input_table = top20
    data = []
    for index, row in input_table.iterrows():
        line = numpy.ndarray.flatten(row.values)
        trace = go.Box(
            y=line[1:]+1,
            name=line[0],
            text=labels
        )
        data.append(trace)
    layout = go.Layout(
        autosize=True,
        margin=go.Margin(
            l=50,
            r=50,
            b=150,
            t=100,
            pad=4
        ),
        title="Top20 microRNA with highest Coefficient of Variation",
        xaxis=dict(
            # title='Nulceotide added',
            tick0=0,
            dtick=1,
        ),
        yaxis=dict(
            type='log',
            title='RPM+1')
    )
    fig = go.Figure(data=data, layout=layout)
    div_obj = plot(fig, show_link=False, auto_open=False, output_type='div')
    return div_obj

    #CVs = (input_table[["CV"]].values)


    print("")

def makeBottom20CV(input_file):
    first_table = pandas.read_table(input_file, sep='\t')
    ordered = first_table.sort_values(by="CV", axis=0, ascending=False)
    clean = ordered.drop(["stddev",	"CV", "mean"],axis=1)
    top20 = clean.tail(20)
    labels = top20.columns[1:]
    input_table = top20
    data = []
    for index, row in input_table.iterrows():
        line = numpy.ndarray.flatten(row.values)
        trace = go.Box(
            y=line[1:]+1,
            name=line[0],
            text=labels
        )
        data.append(trace)
    layout = go.Layout(
        autosize=True,
        margin=go.Margin(
            l=50,
            r=50,
            b=150,
            t=100,
            pad=4
        ),
        title="20 microRNA with lowest Coefficient of Variation",
        xaxis=dict(
            # title='Nulceotide added',
            tick0=0,
            dtick=1,
        ),
        yaxis=dict(
            type='log',
            title='RPM+1')
    )
    fig = go.Figure(data=data, layout=layout)
    div_obj = plot(fig, show_link=False, auto_open=False, output_type='div')
    return div_obj

    #CVs = (input_table[["CV"]].values)


    # print("")
# makeTop20CV("C:/Users/Ernesto/Desktop/Colabo/liqDB/test/miRNA_RPMadjLib_CV_min20.txt")

def makeDEbox(input_file,de_file=None):
    input_file = input_file.replace("\\","/")
    #print((input_file))
    #return None
    #first_table = pandas.read_table(input_file, header=None ,sep='\t')
    pval_dict=dict()
    label_dict=dict()
    if de_file:
        with open(de_file, "r") as de_hand:
            lines = de_hand.readlines()
            lines.pop(0)
            for line in lines:
                row=line.split("\t")
                pval_dict[row[0]] = row[-2]
    color_list= ["red", "green","blue","yellow","purple","orange"]*10
    with open(input_file, "r") as ifile:
        lines = ifile.readlines()
        x_dict = dict()
        y_dict = dict()
        x_list = []
        size_dict = dict()
        for i,line in enumerate(lines):
            row = line.split("\t")
            x,cond = row[0].split("#")
            x_list.append(x)
            if len(set(x_list))< 21:

                if x_dict.get(cond):
                    to_ap = [x]*(len(row)-1)
                    if not size_dict.get(cond):
                        size_dict[cond] = len(to_ap)
                    x_dict[cond].extend(to_ap)
                    y_dict[cond].extend(row[1:])
                    label_dict[cond].extend([pval_dict.get(x)]*(len(row)-1))
                else:
                    x_dict[cond] = [x]*(len(row)-1)
                    y_dict[cond] = row[1:]
                    label_dict[cond] = [pval_dict.get(x)]*(len(row)-1)
        data = []
        for i,key in enumerate(x_dict.keys()):
            to_y = numpy.array(list(map(float, y_dict[key])))
            to_y.astype(float)
            to_y = to_y+1
            trace = go.Box(
                    x=x_dict[key],
                    #y=y_dict[key],
                #numpy.ndarray.flatten(
                    y=to_y,
                    marker=dict(
                        color= color_list[i]),
                    text=label_dict.get(key),
                    name=key + " n=" + str(size_dict[key])
                )
            data.append(trace)
        #    print(data)
        layout = go.Layout(
                boxmode='group',
                autosize=True,
                margin=go.Margin(
                    l=50,
                    r=50,
                    b=150,
                    t=100,
                    pad=4
                ),
                title="Differentially Expressed miRNAs",
                xaxis=dict(
                    # title='Nulceotide added',
                    tick0=0,
                    dtick=1,
                ),
                yaxis=dict(
                    type='log',
                    title='RPM+1')
            )
    fig = go.Figure(data=data, layout=layout)
    div_obj = plot(fig, show_link=False, auto_open=False, output_type='div')
    return div_obj

def makeDEbox_pval(input_file,de_file=None):
    input_file = input_file.replace("\\","/")
    #print((input_file))
    #return None
    #first_table = pandas.read_table(input_file, header=None ,sep='\t')
    pval_dict=dict()
    label_dict=dict()
    if de_file:
        with open(de_file, "r") as de_hand:
            lines = de_hand.readlines()
            lines.pop(0)
            for line in lines:
                row=line.split("\t")
                # pval_dict[row[0]] = str(float(row[-2]))
                pval_dict[row[0]] = str(round(float(row[-2]),8))
    print(pval_dict)
    color_list= ["red", "green","blue","yellow","purple","orange"]*10
    with open(input_file, "r") as ifile:
        lines = ifile.readlines()
        x_dict = dict()
        y_dict = dict()
        x_list = []
        size_dict = dict()
        for i,line in enumerate(lines):
            row = line.split("\t")
            x,cond = row[0].split("#")
            x_list.append(x)
            if len(set(x_list))< 21:

                if x_dict.get(cond):
                    to_ap = ["<b>" + x +"</b>" + " [pval="+ pval_dict.get(x)+"]"] *(len(row)-1)
                    if not size_dict.get(cond):
                        size_dict[cond] = len(to_ap)
                    x_dict[cond].extend(to_ap)
                    y_dict[cond].extend(row[1:])
                    label_dict[cond].extend([pval_dict.get(x)]*(len(row)-1))
                else:
                    x_dict[cond] = [x + " [pval="+ pval_dict.get(x)+"]"]  *(len(row)-1)
                    y_dict[cond] = row[1:]
                    label_dict[cond] = [pval_dict.get(x)]*(len(row)-1)
        data = []
        print(len(label_dict["Group1"]))
        print(len(x_dict["Group1"]))

        for i,key in enumerate(x_dict.keys()):
            to_y = numpy.array(list(map(float, y_dict[key])))
            to_y.astype(float)
            to_y = to_y+1
            trace = go.Box(
                    x=x_dict[key],
                    #y=y_dict[key],
                #numpy.ndarray.flatten(
                    y=to_y,
                    #z=label_dict.get(key),
                    marker=dict(
                        color= color_list[i]),
                    #text=label_dict.get(key),
                    #hovermode="compare",
                    # hoverinfo=label_dict.get(key),
                    #hoveron="points",
                    name=key + " n=" + str(size_dict[key])
                )
            data.append(trace)
        #    print(data)
        layout = go.Layout(
                hovermode="x",
                #hoveron="points",
                boxmode='group',
                autosize=True,
                margin=go.Margin(
                    l=50,
                    r=50,
                    b=150,
                    t=100,
                    pad=4
                ),
                title="Differentially Expressed miRNAs",
                xaxis=dict(
                    # title='Nulceotide added',
                    tick0=0,
                    dtick=1,
                ),
                yaxis=dict(
                    type='log',
                    title='RPM+1')
            )
    fig = go.Figure(data=data, layout=layout)
    div_obj = plot(fig, show_link=False, auto_open=False, output_type='div')

    #plot(fig, filename="C:/Users/Ernesto/Desktop/Groups/test.html", show_link=False, auto_open=False)
    return div_obj

#makeDEbox_pval("C:/Users/Ernesto/Desktop/Groups/matrix_miRNA_RPMadjLib.txt",  "C:/Users/Ernesto/Desktop/Groups/de_miRNA_RPMadjLib_Group1-Group2.txt")

#makeDEbox()


def makeFullDEbox(input_file):
    input_file = input_file.replace("\\","/")
    #print((input_file))
    #return None
    #first_table = pandas.read_table(input_file, header=None ,sep='\t')
    color_list= ["red", "green","blue","yellow","purple","orange"]*10
    with open(input_file, "r") as ifile:
        lines = ifile.readlines()
        x_dict = dict()
        y_dict = dict()
        for i,line in enumerate(lines):
            row = line.split("\t")
            x,cond = row[0].split("#")
            if x_dict.get(cond):
                to_ap = [x]*(len(row)-1)
                x_dict[cond].extend(to_ap)
                y_dict[cond].extend(row[1:])
            else:
                x_dict[cond] = [x]*(len(row)-1)
                y_dict[cond] = row[1:]
        data = []
        for i,key in enumerate(x_dict.keys()):
            trace = go.Box(
                    x=x_dict[key],
                    y=y_dict[key],
                    marker=dict(
                        color= color_list[i]),
                    name=key
                )
            data.append(trace)
        #    print(data)
        layout = go.Layout(
                boxmode='group',
                autosize=True,
                margin=go.Margin(
                    l=50,
                    r=50,
                    b=150,
                    t=100,
                    pad=4
                ),
                title="Differentially Expressed miRNAs",
                xaxis=dict(
                    # title='Nulceotide added',
                    tick0=0,
                    dtick=1,
                ),
                yaxis=dict(
                    type='log',
                    title='RPM')
            )
    fig = go.Figure(data=data, layout=layout)
    div_obj = plot(fig, show_link=False, auto_open=False, output_type='div')
    return div_obj

#makeDEbox("C:/Users/Ernesto/PycharmProjects/liqDB/gentelella/data_folder/studies/SRP062974/de/health_state/matrix_miRNA_RPMadjLib.txt")

def makeMirBox(input_file,title,input_labels=[]):
    input_file = input_file.replace("\\", "/")

    color_list = ["red", "green", "blue", "yellow", "purple", "orange"]
    with open(input_file, "r") as ifile:
        lines = ifile.readlines()
        data = []
        for ix,line in enumerate(lines):
            row = line.split("\t")
            values = row[1:]
            RPM = list(map(float, values))
            RPM1 = [x + 1 for x in RPM]
            labels=""
            if input_labels:
                labels=input_labels[ix][1:]
            if not row[0].replace(" ","") == "" :
                trace = go.Box(
                    y=RPM1,
                    name=row[0] + " (" + str(len(row[1:])) + ")" ,
                    text= labels
                )
                data.append(trace)
        layout = go.Layout(
            boxmode='group',
            autosize=True,
            margin=go.Margin(
                l=50,
                r=50,
                b=150,
                t=100,
                pad=4
            ),
            title= title,
            xaxis=dict(
                # title='Nulceotide added',
                tick0=0,
                dtick=1,
            ),
            yaxis=dict(
                type='log',
                title='RPM+1')
        )
        fig = go.Figure(data=data, layout=layout)
        div_obj = plot(fig, show_link=False, auto_open=False, output_type='div')
        return div_obj