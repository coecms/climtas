#!/bin/bash

set -eu

function run(){
    subt=climtas
    ncpus=$1

    qsub -l ncpus=$ncpus,mem=$(( ncpus * 4 ))gb -o log run_${subt}.sh
}

run 2
