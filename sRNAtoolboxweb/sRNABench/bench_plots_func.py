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
import sys

from .bench_plots_gen import Full_read_length_divs,Read_len_type, Mapping_stat_plot, top_miRs_plot

def full_read_length(input_folder):
    results_list = Full_read_length_divs(input_folder, path_to_venv=PATH_TO_VENV, plotly_script=BENCH_PLOTLY, media_url=MEDIA_URL,
                          media_root=MEDIA_ROOT, png=False)
    return results_list

def read_length_type(input_folder):
    results_list = Read_len_type(input_folder, path_to_venv=PATH_TO_VENV, plotly_script=BENCH_PLOTLY, media_url=MEDIA_URL,
                          media_root=MEDIA_ROOT, png=False)
    return results_list

def mapping_stat(input_folder):
    results_list = Mapping_stat_plot(input_folder, path_to_venv=PATH_TO_VENV, plotly_script=BENCH_PLOTLY, media_url=MEDIA_URL,
                          media_root=MEDIA_ROOT, png=False)
    return results_list

def top_miRNA_plot(input_file,title):
    results_list = top_miRs_plot(input_file,title, path_to_venv=PATH_TO_VENV, plotly_script=BENCH_PLOTLY, media_url=MEDIA_URL,
                          media_root=MEDIA_ROOT, png=False)
    return results_list

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
def main():
    p_type = sys.argv[1]
    input_par = sys.argv[2]

    if p_type == "readLength":
        Full_read_length_divs(input_par, png=True )
        print("wtf")
