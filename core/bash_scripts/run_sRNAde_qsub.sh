#!/bin/bash
#PBS -l walltime=24:30,mem=4Gb


source virtualenvs/srantoolbox/bin/activate
runPipelines $c

