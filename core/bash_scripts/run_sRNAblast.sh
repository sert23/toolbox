#!/bin/bash
#PBS -l walltime=180:00:00,mem=9Gb

export PYTHONPATH=/shared/
export BLASTDB=/shared/blastDB/
python /shared/sRNAtoolbox/core/pipelines/runPipelines.py $key $name $outdir $pipeline -c $configure