#!/bin/bash
#PBS -l walltime=72:00:00,mem=6Gb

export PYTHONPATH=/shared/
cd $outdir
python /shared/sRNAtoolbox/core/pipelines/runPipelines.py $key $name $outdir $pipeline --program_string $program_string --mirna_file $miRNA_file --parameter_string $parameter_string --utr_file $utr_file --species $go_table
