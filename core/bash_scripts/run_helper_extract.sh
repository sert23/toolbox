#!/bin/bash
#PBS -l walltime=72:00:00,mem=6Gb

export PYTHONPATH=/shared/
workon dev
runPipelines $key $name $outdir $pipeline --mode $mode --inputfile $inputfile --string $string

