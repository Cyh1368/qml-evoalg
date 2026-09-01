#!/bin/bash
# Run ONCE on a Bouchet login node to build the conda env the array jobs use.
# Usage (on Bouchet):  bash setup_env.sh
set -euo pipefail

module purge
module load miniconda

if conda env list | grep -q '^qml-ea'; then
    echo "env qml-ea already exists"
else
    conda create -y -n qml-ea python=3.11
fi

conda activate qml-ea
pip install --upgrade pip
pip install "pennylane==0.45.0" numpy matplotlib

python -c "import pennylane as qml, numpy; print('pennylane', qml.__version__, 'numpy', numpy.__version__)"
echo "ENV READY"
