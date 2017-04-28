#!/bin/bash
#PBS -l walltime=72:00:00,mem=100Mb

export PYTHONPATH=/shared/
python /shared/sRNAtoolbox/core/pipelines/runPipelines.py $key $name $outdir $pipeline --bench_id $bench_id