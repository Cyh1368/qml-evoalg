#!/bin/bash
#SBATCH --job-name=shotcert-phys
#SBATCH --partition=devel
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=6000M
#SBATCH --time=04:00:00
#SBATCH --output=/home/cpsc4710_ch2499/qml-evoalg/shotcert/results/log_physics_%j.out
set -eu
cd /home/cpsc4710_ch2499/qml-evoalg
module reset
module load Python/3.12.3-GCCcore-13.3.0 SciPy-bundle/2024.05-gfbf-2024a
export LD_LIBRARY_PATH=/apps/software/2024a/software/Python/3.12.3-GCCcore-13.3.0/lib:${LD_LIBRARY_PATH:-}
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python3 -m shotcert.experiments.exp_physics --reps 150 --out shotcert/results/physics.json
