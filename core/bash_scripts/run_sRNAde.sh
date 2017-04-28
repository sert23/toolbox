#!/bin/bash
#PBS -l walltime=24:30,mem=4Gb

export PYTHONPATH=/shared/
python /shared/sRNAtoolbox/core/pipelines/runPipelines.py $key $name $outdir $pipeline -g $group -i $input --iso $iso --nt $nt --dt $dt --hmTop $hmTop --hmPerc $hmPerc

