#!/bin/bash
#PBS -l walltime=24:30,mem=4Gb


source /opt/venv/sRNAtoolbox2017/bin/activate
export PATH=$PATH:/usr/local/bin:/usr/bin
runPipelines $c

