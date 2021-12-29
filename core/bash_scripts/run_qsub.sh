#!/bin/bash
#PBS -l walltime=24:30:00,mem=50Gb



source /opt/venv/sRNAtoolbox2019/bin/activate
export PATH=$PATH:/usr/local/bin:/usr/bin
runPipelines $c

