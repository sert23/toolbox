#!/bin/bash
#PBS -l walltime=72:00:00,mem=6Gb

export PYTHONPATH=/shared/
python /shared/sRNAtoolbox/core/pipelines/runPipelines.py $key $name $outdir $pipeline --mode $mode  --species $species