#!/bin/bash
#PBS -l walltime=90:30,mem=6Gb

export PYTHONPATH=/shared/
workon dev
runPipelines $key $name $outdir $pipeline  -i $input --minReadLength $minReadLength --maxReadLength $maxReadLength --microRNA $microRNA --minRC $minRC --noMM $noMM

