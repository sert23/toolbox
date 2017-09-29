#!/bin/bash
#PBS -l walltime=72:00:00,mem=6Gb

export PYTHONPATH=/shared/
cd $outdir
workon dev
runPipelines $key $name $outdir $pipeline --parameter_string $parameter_string --program_string $program_string --mirna_file $miRNA_file --utr_file $utr_file