# Import libraries
import itertools
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from plotly.offline import plot


def general_plot(input_file, x_lab, y_lab, title):

    try:
        input_table = pd.read_table(input_file, sep='\t')
        col_names = list(input_table.columns[1:])
        input_table.ix[:, 0] = input_table.ix[:, 0].apply(lambda x: x[:20] + '...' if len(x) > 20 else x)

        layout = go.Layout(
            autosize=True,
            width=1050,
            height=580,
            margin=go.layout.Margin(
                l=100,
                r=50,
                b=150,
                t=100,
                pad=4
            ),
            title=title,
            font=dict(size=13),
            xaxis=dict(
                title=x_lab,
            ),
            yaxis=dict(
                title=y_lab),
            hovermode='closest'
        )

        data = []
        for index, row in input_table.iterrows():

            data.append(go.Box(
                y=row.values[1:],
                text=col_names,
                name=str(row.values[0]),
                marker=dict(
                ),
                hoverinfo='text+name+y'
            ))

        fig = go.Figure(data=data, layout=layout)
        div_obj = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)
        return div_obj

    except:
        return None


def general_plot_cols(input_file, x_lab, y_lab, title):

    try:
        input_table = pd.read_table(input_file, sep='\t')
        input_table = input_table.transpose().reset_index()
        input_table = input_table.rename(columns=input_table.iloc[0]).drop(input_table.index[0])
        col_names = list(input_table.columns[1:])
        input_table.ix[:, 0] = input_table.ix[:, 0].apply(name_shorter)

        layout = go.Layout(
            autosize=True,
            width=1050,
            height=580,
            margin=go.layout.Margin(
                l=100,
                r=50,
                b=150,
                t=100,
                pad=4
            ),
            title=title,
            font=dict(size=13),
            xaxis=dict(
                title=x_lab,
            ),
            yaxis=dict(
                title=y_lab),
            hovermode='closest'
        )

        data = []
        for index, row in input_table.iterrows():

            data.append(go.Box(
                y=row.values[1:],
                text=col_names,
                name=str(row.values[0]),
                marker=dict(
                ),
                hoverinfo='text+name+y'
            ))

        fig = go.Figure(data=data, layout=layout)
        div_obj = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)
        return div_obj

    except:
        return None


def make_seq_plot(input_file):

    try:
        input_table = pd.read_table(input_file, index_col=0, sep='\t')
        row_names = list(input_table.index)
        colors = ['rgb(31, 119, 180)', 'rgb(255, 144, 14)', 'rgb(44, 160, 101)', 'rgb(255, 65, 54)',
                  'rgb(149, 104, 190)', 'rgb(140, 86, 75)', 'rgb(227, 119, 194)', 'rgb(127, 127, 127)',
                  'rgb(23, 190, 207)']

        trace0 = go.Box(
            y=np.ndarray.flatten(input_table[['raw reads']].values),
            text=row_names,
            name='Raw Reads',
            boxpoints='outliers',
            marker=dict(
                color=colors[0],
            ),
            hoverinfo='text+name+y'
        )

        trace1 = go.Box(
            y=np.ndarray.flatten(input_table[['adapter cleaned']].values),
            text=row_names,
            name='Adapter cleaned',
            marker=dict(
                color=colors[1],
            ),
            hoverinfo='text+name+y'
        )

        trace2 = go.Box(
            y=np.ndarray.flatten(input_table[['reads in analysis']].values),
            text=row_names,
            name='Reads in analysis',
            marker=dict(
                color=colors[2],
            ),
            hoverinfo='text+name+y'
        )

        trace3 = go.Box(
            y=np.ndarray.flatten(input_table[['unique reads in analysis']].values),
            text=row_names,
            name='Unique reads in analysis',
            marker=dict(
                color=colors[3],
            ),
            hoverinfo='text+name+y'
        )
        if "---" not in list(itertools.chain(*input_table[['genome mapped reads']].values)):
            trace4 = go.Box(
                y=np.ndarray.flatten(input_table[['genome mapped reads']].values),
                text=row_names,
                name='Genome mapped reads',
                marker=dict(
                    color=colors[4],
                ),
                hoverinfo='text+name+y'
            )
        else:
            trace4 = None

        if "---" not in list(itertools.chain(*input_table[['assignedRC']].values)):
            trace4_1 = go.Box(
                y=np.ndarray.flatten(input_table[['assignedRC']].values),
                text=row_names,
                name='Assigned Reads',
                marker=dict(
                    color=colors[5],
                ),
                hoverinfo='text+name+y'
            )
        else:
            trace4_1 = None

        if "---" not in list(itertools.chain(*input_table[['unique reads mapped to genome']].values)):
            trace5 = go.Box(
                y=np.ndarray.flatten(input_table[['unique reads mapped to genome']].values),
                text=row_names,
                name='Unique reads mapped to genome',
                marker=dict(
                    color=colors[6],
                ),
                hoverinfo='text+name+y'
            )
        else:
            trace5 = None

        trace6 = go.Box(
            y=np.ndarray.flatten(input_table[['QualityFilteredReads']].values),
            text=row_names,
            name='Quality filtered Reads',
            marker=dict(
                color=colors[7],
            ),
            hoverinfo='text+name+y'
        )

        trace7 = go.Box(
            y=np.ndarray.flatten(input_table[['mature_microRNA_reads']].values),
            text=row_names,
            name='microRNA mapped reads',
            marker=dict(
                color=colors[8],
            ),
            hoverinfo='text+name+y'
        )

        layout = go.Layout(
            autosize=True,
            margin=go.layout.Margin(
                l=100,
                r=50,
                b=200,
                t=100,
                pad=4
            ),
            title="Sequencing statistics",
            font=dict(size=13),
            yaxis=dict(title='Number of reads'),
            hovermode='closest'
        )

        data = []
        for trace in [trace0, trace1, trace2, trace3, trace4, trace4_1, trace5, trace6, trace7]:
            if trace:
                data.append(trace)

        fig = go.Figure(data=data, layout=layout)
        div_obj = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)
        return div_obj

    except:
        return None


def make_rel_plot(input_file):

    try:
        input_table = pd.read_table(input_file, index_col=0, sep='\t')
        row_names = list(input_table.index)

        trace1 = go.Box(
            y=100*np.ndarray.flatten(np.array(input_table[["adapter cleaned"]].values, dtype=float)) /
            np.ndarray.flatten(input_table[["raw reads"]].values),
            text=row_names,
            name='Adapter cleaned',
            marker=dict(
                color='rgb(255, 144, 14)',
            ),
            hoverinfo='text+name+y'
        )

        trace2 = go.Box(
            y=100*np.ndarray.flatten(np.array(input_table[["reads in analysis"]].values, dtype=float)) /
            np.ndarray.flatten(input_table[["raw reads"]].values),
            text=row_names,
            name='Reads in analysis',
            marker=dict(
                color='rgb(44, 160, 101)',
            ),
            hoverinfo='text+name+y'
        )
        trace3 = go.Box(
            y=100*np.ndarray.flatten(np.array(input_table[["QualityFilteredReads"]].values, dtype=float)) /
            np.ndarray.flatten(input_table[["raw reads"]].values),
            text=row_names,
            name='Quality filtered Reads',
            marker=dict(
                color='rgb(255, 65, 54)',
            ),
            hoverinfo='text+name+y'
        )

        if not ("---" in list(itertools.chain(*input_table[["genome mapped reads"]].values))):
            trace4 = go.Box(
                y=100*np.ndarray.flatten(np.array(input_table[["genome mapped reads"]].values, dtype=float)) /
                np.ndarray.flatten(input_table[["reads in analysis"]].values),
                text=row_names,
                name='Genome mapped reads',
                marker=dict(
                    color='rgb(149, 104, 190)'
                ),
                hoverinfo='text+name+y'
            )
        else:
            trace4 = None

        if "---" not in list(itertools.chain(*input_table[["assignedRC"]].values)):
            trace4_1 = go.Box(
                y=100*np.ndarray.flatten(np.array(input_table[["assignedRC"]].values, dtype=float)) /
                np.ndarray.flatten(input_table[["reads in analysis"]].values),
                text=row_names,
                name='Assigned reads',
                marker=dict(
                    color='rgb(140, 86, 75)',
                ),
                hoverinfo='text+name+y'
            )
        else:
            trace4_1 = None

        if "---" not in list(itertools.chain(*input_table[["mature_microRNA_reads"]].values)):
            trace7 = go.Box(
                y=100*np.ndarray.flatten(np.array(input_table[["mature_microRNA_reads"]].values, dtype=float)) /
                np.ndarray.flatten(input_table[["reads in analysis"]].values),
                text=row_names,
                name='microRNA mapped reads',
                marker=dict(
                    color='rgb(23, 190, 207)',
                ),
                hoverinfo='text+name+y'
            )
        else:
            trace7 = None

        layout = go.Layout(
            autosize=True,
            margin=go.layout.Margin(
                l=100,
                r=50,
                b=200,
                t=100,
                pad=4
            ),
            title="Sequencing statistics (relative)",
            xaxis=dict(title=''),
            yaxis=dict(title='Percentage of reads'),
            font=dict(size=13),
            hovermode='closest'
        )

        data = []
        for l in [trace1, trace2, trace3, trace4, trace4_1, trace7]:
            if l:
                data.append(l)

        fig = go.Figure(data=data, layout=layout)
        div_obj = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)
        return div_obj

    except:
        return None


def make_map_plot(input_file):

    try:
        input_table = pd.read_table(input_file, sep='\t')
        col_names = list(input_table.columns[1:])
        n_categories = len(input_table.index)
        colors = ['(255, 144, 14)', '(43, 183, 47)', '(253, 56, 34)', '(250, 250, 51)', '(31, 119, 180)',
                  '(145, 145, 145)', '(23, 190, 207)', '(196, 57, 212)']
        box_plot_colors = []

        for i in itertools.islice(itertools.cycle(colors), n_categories):
            box_plot_colors.append(i)

        layout = go.Layout(
            autosize=True,
            margin=go.layout.Margin(
                l=100,
                r=50,
                b=150,
                t=100,
                pad=4
            ),
            title='Mapping statistics',
            font=dict(size=13),
            xaxis=dict(
                title='Categories',
            ),
            yaxis=dict(
                title='Reads Per Million (RPM)'),
            hovermode='closest'
        )

        data = []
        for index, row in input_table.iterrows():
            if index > 0:
                data.append(go.Box(
                    y=row.values[1:],
                    text=col_names,
                    name=row.values[0],
                    marker=dict(
                        color='rgb'+box_plot_colors[index-1],
                    ),
                    hoverinfo='text+name+y'
                ))

        fig = go.Figure(data=data, layout=layout)
        div_obj = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)
        return div_obj

    except:
        return None


def make_length_plot(input_file):

    try:
        input_table = pd.read_table(input_file, sep='\t')
        col_names = list(input_table.columns[1:])
        index_row = list(input_table['name'])

        data = []
        for i in range(min(index_row), max(index_row)+1):  # Read length range to show
            data.append(go.Box(
                y=np.ndarray.flatten(input_table.loc[input_table["name"] == i].values)[1:],
                text=col_names,
                name=str(i),
                marker=dict(
                    color='rgb(0,0,139)',
                ),
                hoverinfo='text+y'
            ))

        layout = go.Layout(
            autosize=True,
            width=1050,
            height=580,
            margin=go.layout.Margin(
                l=100,
                r=50,
                b=150,
                t=100,
                pad=4
            ),
            title='Read length distribution (analysis)',
            font=dict(size=13),
            xaxis=dict(
                title='Read Length (nt)',
            ),
            yaxis=dict(
                title='Percentage (%)'),
            hovermode='closest'
        )

        fig = go.Figure(data=data, layout=layout)
        div_obj = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)
        return div_obj

    except:
        return None


def make_full_length_plot(input_file):

    try:
        input_table = pd.read_table(input_file, sep='\t')
        col_names = list(input_table.columns[1:])
        index_row = list(input_table['name'])

        data = []
        for i in range(min(index_row), max(index_row)+1):  # Read length range to show
            data.append(go.Box(
                y=np.ndarray.flatten(input_table.loc[input_table["name"] == i].values)[1:],
                text=col_names,
                name=str(i),
                marker=dict(
                    color='rgb(0,0,139)',
                ),
                hoverinfo='text+y'
            ))

        layout = go.Layout(
            autosize=True,
            width=1050,
            height=580,
            margin=go.layout.Margin(
                l=100,
                r=50,
                b=150,
                t=100,
                pad=4
            ),
            title='Read length distribution (full)',
            font=dict(size=13),
            xaxis=dict(
                title='Read Length (nt)',
            ),
            yaxis=dict(
                title='Percentage (%)'),
            hovermode='closest'
        )

        fig = go.Figure(data=data, layout=layout)
        div_obj = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)
        return div_obj

    except:
        return None


def make_length_genome_plot(input_file):

    try:
        input_table = pd.read_table(input_file, sep='\t')
        col_names = list(input_table.columns[1:])
        index_row = list(input_table['name'])

        data = []
        for i in range(min(index_row), max(index_row)+1):  # Read length range to show
            data.append(go.Box(
                y=np.ndarray.flatten(input_table.loc[input_table["name"] == i].values)[1:],
                text=col_names,
                name=str(i),
                marker=dict(
                    color='rgb(0,0,139)',
                ),
                hoverinfo='text+y'
            ))

        layout = go.Layout(
            autosize=True,
            width=1050,
            height=580,
            margin=go.layout.Margin(
                l=100,
                r=50,
                b=150,
                t=100,
                pad=4
            ),
            title='Read length distribution (genome Mapped)',
            font=dict(size=13),
            xaxis=dict(
                title='Read Length (nt)',
            ),
            yaxis=dict(
                title='Percentage (%)'),
            hovermode='closest'
        )

        fig = go.Figure(data=data, layout=layout)
        div_obj = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)
        return div_obj

    except:
        return None


def make_NTA_plot(input_file):

    try:
        input_table = pd.read_table(input_file, sep='\t')
        col_names = list(input_table.columns[1:])

        data = []
        color_dict = {"A": "rgb(255,0,0)", "C": "rgb(0,255,0)", "T": "rgb(0,0,255)", "G": "rgb(255,255,0)"}
        for n in ["A", "C", "T", "G"]:
            data.append(go.Box(
                y=np.ndarray.flatten(input_table.loc[input_table["name"] == n].values)[1:]*100,
                text=col_names,
                name='nta-'+n,
                marker=dict(
                    color=color_dict[n],
                ),
                hoverinfo='text+y'
            ))

        layout = go.Layout(
            autosize=True,
            margin=go.layout.Margin(
                l=100,
                r=50,
                b=150,
                t=100,
                pad=4
            ),
            title='Non-templated additions',
            font=dict(size=13),
            xaxis=dict(
                title='Nucleotide added',
                tick0=0,
                dtick=1,
            ),
            yaxis=dict(
                title='Percentage of reads (%)'),
            hovermode='closest'
        )

        fig = go.Figure(data=data, layout=layout)
        div_obj = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)
        return div_obj

    except:
        return None


def make_isomir_plot(input_file):

    try:
        input_table = pd.read_table(input_file, sep='\t')
        col_names = list(input_table.columns[1:])

        data = []
        iterables = input_table[["name"]].values
        iterables = [item for sublist in iterables for item in sublist]
        iterables.remove("nta|AU")
        iterables.remove("nta|UA")
        for i in iterables:
            data.append(go.Box(
                y=np.ndarray.flatten(input_table.loc[input_table["name"] == i].values)[1:]*100,
                text=col_names,
                name=i,
                hoverinfo='text+y'
            ))

        layout = go.Layout(
            autosize=True,
            margin=go.layout.Margin(
                l=100,
                r=50,
                b=150,
                t=100,
                pad=4
            ),
            title='isomiRs distribution (other variants)',
            font=dict(size=13),
            xaxis=dict(
                title='isomiR variant type',
                tick0=0,
                dtick=1,
            ),
            yaxis=dict(
                title='Percentage of reads (%)'),
            hovermode='closest'
        )

        fig = go.Figure(data=data, layout=layout)
        div_obj = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)
        return div_obj

    except:
        return None


def make_top_exp(input_file, topn):

    try:
        input_table = pd.read_table(input_file, sep='\t')
        col_names = list(input_table.columns[1:])

        data = []
        meanvals = (input_table.mean(axis=1))
        input_table["meanval"] = pd.Series(meanvals)
        ordered = input_table.sort_values(by="meanval", axis=0, ascending=False)
        for i in range(0, topn):
            line = np.ndarray.flatten(np.array(ordered.iloc[i]))
            data.append(go.Box(
                y=line[1:],
                text=col_names,
                name=line[0],
                hoverinfo='text+name+y'
            ))

        layout = go.Layout(
            autosize=True,
            margin=go.layout.Margin(
                l=100,
                r=50,
                b=150,
                t=100,
                pad=4
            ),
            title='Top '+str(topn)+' expressed miRNAs',
            font=dict(size=13),
            yaxis=dict(
                title='Reads Per Million (RPM)'),
            hovermode='closest'
        )

        fig = go.Figure(data=data, layout=layout)
        div_obj = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)
        return div_obj

    except:
        return None


def make_top_CoV(input_file, topn):

    try:
        input_table = pd.read_table(input_file, sep='\t')
        col_names = list(input_table.columns[1:])

        data = []
        meanvals = (input_table.mean(axis=1))
        stdvals = input_table.std(axis=1)
        CVvals = stdvals/meanvals
        input_table["CV"] = pd.Series(CVvals)
        ordered = input_table.sort_values(by="CV", axis=0, ascending=False)
        CVs = input_table[["CV"]].values
        xticks = [item for sublist in CVs for item in sublist][0:topn]
        for i in range(0, topn):
            line = np.ndarray.flatten(np.array(ordered.iloc[i]))
            data.append(go.Box(
                y=np.float64(line[1:-1]),
                text=col_names,
                name=line[0]+"<br>"+str(round(np.float64(line[-1]), 2)),
                hoverinfo='text+name+y'
            ))

        layout = go.Layout(
            autosize=True,
            margin=go.layout.Margin(
                l=100,
                r=50,
                b=150,
                t=100,
                pad=4
            ),
            title='Top '+str(topn)+' miRNAs with the highest variation (CoV)',
            font=dict(size=13),
            xaxis2=dict(
                ticktext=[str(i) for i in xticks],
                overlaying='x',
                side='top',
                tickmode='auto'
            ),
            yaxis=dict(
                title='Reads Per Million in logscale (RPM)',
                type='log',
                autorange=True
            ),
            hovermode='closest',
        )

        fig = go.Figure(data=data, layout=layout)
        div_obj = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)
        return div_obj

    except:
        return None


def make_bottom_CoV(input_file, topn):

    try:
        input_table = pd.read_table(input_file, sep='\t')
        col_names = list(input_table.columns[1:])

        data = []
        meanvals = (input_table.mean(axis=1))
        stdvals = input_table.std(axis=1)
        CVvals = stdvals/meanvals
        input_table["CV"] = pd.Series(CVvals)
        ordered = input_table.sort_values(by="CV", axis=0, ascending=True)
        for i in range(0, topn):
            line = np.ndarray.flatten(np.array(ordered.iloc[i]))
            data.append(go.Box(
                y=np.float64(line[1:-1]),
                text=col_names,
                name=line[0]+"<br>"+str(round(np.float64(line[-1]), 2)),
                hoverinfo='text+name+y'
            ))

        layout = go.Layout(
            autosize=True,
            margin=go.layout.Margin(
                l=100,
                r=50,
                b=150,
                t=100,
                pad=4
            ),
            title='Bottom '+str(topn)+' miRNAs with the lowest variation (CoV)',
            font=dict(size=13),
            yaxis=dict(
                title='Reads Per Million in logscale (RPM)',
                type='log'
            ),
            hovermode='closest',
        )

        fig = go.Figure(data=data, layout=layout)
        div_obj = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)
        return div_obj

    except:
        return None


def make_top_NTAA_plot(input_file, topn):

    try:
        input_table = pd.read_table(input_file, sep='\t')
        col_names = list(input_table.columns[1:])

        data = []
        meanvals = (input_table.mean(axis=1))
        input_table["meanvals"] = pd.Series(meanvals)
        ordered = input_table.sort_values(by="meanvals", axis=0, ascending=False)
        for i in range(0, topn):
            line = np.ndarray.flatten(np.array(ordered.iloc[i]))
            data.append(go.Box(
                y=np.float64(line[1:-1]),
                text=col_names,
                name=line[0],
                hoverinfo='text+name+y'
            ))

        layout = go.Layout(
            autosize=True,
            margin=go.layout.Margin(
                l=100,
                r=50,
                b=150,
                t=100,
                pad=4
            ),
            title='Top '+str(topn)+' miRNAs with the highest fraction of NTA-A',
            font=dict(size=13),
            yaxis=dict(
                title='Fraction of reads assigned to specific miRNA',
            ),
            hovermode='closest'
        )

        fig = go.Figure(data=data, layout=layout)
        div_obj = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)
        return div_obj

    except:
        return None


def make_top_NTAU_plot(input_file, topn):

    try:
        input_table = pd.read_table(input_file, sep='\t')
        col_names = list(input_table.columns[1:])

        data = []
        meanvals = (input_table.mean(axis=1))
        input_table["meanvals"] = pd.Series(meanvals)
        ordered = input_table.sort_values(by="meanvals", axis=0, ascending=False)
        for i in range(0, topn):
            line = np.ndarray.flatten(np.array(ordered.iloc[i]))
            data.append(go.Box(
                y=np.float64(line[1:-1]),
                text=col_names,
                name=line[0],
                hoverinfo='text+name+y'
            ))

        layout = go.Layout(
            autosize=True,
            margin=go.layout.Margin(
                l=100,
                r=50,
                b=150,
                t=100,
                pad=4
            ),
            title='Top '+str(topn)+' miRNAs with the highest fraction of NTA-U',
            font=dict(size=13),
            yaxis=dict(
                title='Fraction of reads assigned to specific miRNA',
            ),
            hovermode='closest'
        )

        fig = go.Figure(data=data, layout=layout)
        div_obj = plot(fig, show_link=False, auto_open=False, output_type='div')
        return div_obj

    except:
        return None


def make_genome_dist_plot(input_file):

    try:
        input_table = pd.read_table(input_file, sep='\t')
        col_names = list(input_table.columns[1:])

        data = []
        for i in input_table["name"]:
            data.append(go.Box(
                y=np.ndarray.flatten(input_table.loc[input_table["name"] == i].values)[1:],
                text=col_names,
                name=str(i),
                hoverinfo='text+name+y'
            ))

        layout = go.Layout(
            autosize=True,
            margin=go.layout.Margin(
                l=100,
                r=50,
                b=150,
                t=100,
                pad=4
            ),
            title='Genome Distribution',
            font=dict(size=13),
            xaxis=dict(
                title='',
                tick0=0,
                dtick=1,
            ),
            yaxis=dict(
                title='Percentage of reads (%)'),
            hovermode='closest'
        )

        fig = go.Figure(data=data, layout=layout)
        div_obj = plot(fig, show_link=False, auto_open=False, output_type='div', include_plotlyjs=False)
        return div_obj

    except:
        return None


# # Call functions
# make_seq_plot(seqstatfile)
# make_rel_plot(seqstatfile)
# make_map_plot(mapstatfile)
# make_length_plot(lengthfile)
# make_full_length_plot(lengthfileF)
# make_NTA_plot(NTAfile)
# make_isomir_plot(isoVarfile)
# make_top_exp(RPMfile, 10)
# make_top_CoV(RPMfile, 10)
# make_bottom_CoV(RPMfile, 10)
# make_top_NTAA_plot(Afile, 20)
# make_top_NTAU_plot(Ufile, 20)
# make_genome_dist_plot(genomeDistfile)
