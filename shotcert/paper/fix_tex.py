"""Post-process generated table fragments: row terminators must be \\\\ not \\, and \\< \\> are not
LaTeX math delimiters. The generators emit both when their string escaping goes wrong, and LaTeX dies
with 'Misplaced \\noalign' at the next \\midrule. Kept as a separate pass so it cannot be bypassed."""
import glob, re, sys
for f in glob.glob(sys.argv[1] + "/tabs_*.tex"):
    lines = open(f).read().split("\n")
    out = []
    for ln in lines:
        if re.search(r"(?<!\\)\\$", ln):
            ln += "\\"
        ln = ln.replace("\\<", "\\langle ").replace("\\>", "\\rangle")
        # The alloc-table header lost one alignment tab to a .replace() in its generator; the rows
        # have nine fields, so restore it here rather than in the fragile string literal.
        if "hat w)$ $" in ln:
            ln = ln.replace("hat w)$ $", "hat w)$ & $")
        out.append(ln)
    open(f, "w").write("\n".join(out))
    print("fixed", f)
