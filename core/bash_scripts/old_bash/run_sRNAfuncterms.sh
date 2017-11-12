#!/bin/bash
#PBS -l walltime=72:04:30,mem=4Gb

export PYTHONPATH=/shared/
workon dev
runPipelines $key $name $outdir $pipeline -a $annot -i $input -t $type --specie $go_table --exp $exp

