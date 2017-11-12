#!/bin/bash
#PBS -l walltime=180:00:00,mem=9Gb

export PYTHONPATH=/shared/
export BLASTDB=/shared/blastDB/
workon dev
runPipelines $key $name $outdir $pipeline -c $configure