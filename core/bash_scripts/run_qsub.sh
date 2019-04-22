#!/bin/bash
#PBS -l walltime=24:30:00,mem=8Gb


source /opt/venv/srnatoolbox2019/bin/activate
export PATH=$PATH:/usr/local/bin:/usr/bin
runPipelines $c

