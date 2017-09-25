#!/bin/bash
#PBS -l walltime=72:00:00,mem=9Gb

export PYTHONPATH=/shared/
workon dev
runPipelines $key $name $outdir $pipeline -c $configure
