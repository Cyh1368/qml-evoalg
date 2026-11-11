#!/bin/bash
# Preview-compile research/paper/main.tex with the standard article class when the
# official neurips_2024.sty is unavailable.  This validates that the body, tables, math
# and thebibliography are valid LaTeX; it is NOT the submission format.
#
#   sbatch --output logs/preview-%j.out research/paper/job_preview.sh
#SBATCH --job-name=preview
#SBATCH --partition=devel
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:20:00
#SBATCH --output=logs/preview-%j.out
set -uo pipefail
module reset
module load texlive/20240312-GCC-13.3.0
cd "${REPO:-$SLURM_SUBMIT_DIR}"
SRC=research/paper/main.tex
BUILD=build/preview
mkdir -p "$BUILD"
python3 - "$SRC" "$BUILD/main_preview.tex" <<'PY'
import re, sys
src, dst = sys.argv[1], sys.argv[2]
text = open(src).read()
shim = (r"\documentclass[11pt]{article}" "\n"
        r"\usepackage[margin=1in]{geometry}" "\n"
        r"\usepackage{booktabs,amsmath,amssymb,mathtools,enumitem,microtype,hyperref,xcolor}" "\n"
        r"\usepackage[utf8]{inputenc}" "\n"
        r"\setlength{\parindent}{0pt}\setlength{\parskip}{4pt}" "\n")
text = re.sub(r"\\documentclass\{[^}]*\}\n", lambda _m: shim, text, count=1)
# the NeurIPS style defines \linebreak-style-free title helpers; article has them too
open(dst, "w").write(text)
print("wrote", dst)
PY
cd "$BUILD"
pdflatex -interaction=nonstopmode main_preview.tex | tail -40 || true
pdflatex -interaction=nonstopmode main_preview.tex | tail -12 || true
echo "preview PDF: $BUILD/main_preview.pdf"
cp main_preview.pdf "$OLDPWD/research/paper/preview_article.pdf" 2>/dev/null || true
