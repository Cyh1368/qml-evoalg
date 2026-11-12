#!/bin/bash
#SBATCH --job-name=shotcert-pdf
#SBATCH --partition=devel
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=2000M
#SBATCH --time=00:20:00
#SBATCH --output=/home/cpsc4710_ch2499/qml-evoalg/shotcert/paper/log_pdf_%j.out
set -eux
cd /home/cpsc4710_ch2499/qml-evoalg/shotcert/paper
module reset
module load texlive/20240312-GCC-13.3.0
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
pdfinfo main.pdf | egrep "Pages|File size"
echo "undefined refs: $(grep -c "undefined" main.log || true)  errors: $(grep -c "LaTeX Error" main.log || true)"
