#!/bin/bash
#PBS -l walltime=24:30,mem=4Gb

export PYTHONPATH=/shared/
source virtualenvs/srantoolbox/bin/activate
runPipelines $1

