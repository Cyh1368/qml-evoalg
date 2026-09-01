"""Label every patch note (patch_name + patch_description) for symmetry talk.

The task's symmetry is qubit-permutation symmetry: the 28 binary features are
the 28 unordered qubit pairs, so relabelling the 8 wires permutes the features
and leaves the label invariant.  A circuit expresses it with a complete-graph
(all-28-pairs) entangler; collective (single-angle) rotation layers are the
matching 1-qubit ingredient.

Each note gets a set of flags:
    names_perm   explicit permutation vocabulary (permutation / equivariant /
                 invariant under relabelling / S_8 / vertex symmetry)
    all_pairs    describes a complete-graph / all-to-all / every-pair entangler
                 as something it is building (negated mentions excluded)
    collective   describes rotations tied across all 8 wires
    task_pairs   notices the feature map itself is an all-pairs / 28-edge object
    partial_sym  only a smaller symmetry: mirror, parity, even/odd, pair-tying
    breaks_sym   explicitly breaks / relaxes a symmetry it names
    none         no symmetry talk at all

Derived: claims_symmetry = names_perm or all_pairs  (the note says it is going
for the full permutation structure), hints_symmetry = claims or collective or
task_pairs (the ingredients are named without the concept).
"""
from __future__ import annotations
import json, os, re, glob
from label_circuits import load_run, classify, extract_spec, norm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PERM = re.compile(r"""(
    permutation(al)?[- ]?(symmetr\w*|invarian\w*|equivarian\w*|aware|group)?
  | permutation
  | equivarian\w*
  | invariant\s+under\s+(the\s+)?(full\s+)?(qubit|wire|vertex|any|every|all)\b[^.]{0,40}
  | commute[s]?\s+with\s+(qubit|wire|vertex)\s+relabel\w*
  | relabel\w*
  | qubit[- ]exchange\w*
  | interchange\w*\s+(of\s+)?(qubits|wires)
  | \bS_?8\b
  | vertex[- ](symmetr\w*|ordering|permutation)
  | (wire|qubit|index)[- ](agnostic|order\w*\s+(does\s+not|doesn't)\s+matter)
  | graph[- ]like\s+symmetr\w*
)""", re.I | re.X)

ALLPAIRS = re.compile(r"""(
    all[- ]to[- ]all
  | complete[- ](graph|entangl\w*|CZ|network)
  | complete\s+(CZ|entangl\w*|graph)
  | \bK[_ ]?8\b
  | every\s+unordered\s+(qubit\s+|wire\s+)?pair
  | all\s+(the\s+)?(qubit|wire)[- ]pairs
  | all[- ]pairs\s+(feature|encoding|representation|structure|coverage|interaction)
  | all\s+28\b | 28\s+CZ | 28\s+(unordered\s+)?pairs
  | fully[- ]connected\s+(graph|entangl\w*|topolog\w*|layer)
  | seven\s+(disjoint\s+)?(perfect\s+)?matchings
  | round[- ]robin\s+matchings
)""", re.I | re.X)

COLLECTIVE = re.compile(r"""(
    collective\w*
  | global\s+(rotation|mixer|angle|parameter|RX|RY|RZ|transverse)
  | (all|every)\s+(8\s+|eight\s+)?(qubits?|wires?)\s+shar\w*
  | shar\w*\s+across\s+all\s+(8\s+|eight\s+)?(qubits?|wires?)
  | (single|one)\s+(shared\s+)?(angle|parameter)\s+(for|across)\s+(all|every|the\s+whole)
  | tied?\s+across\s+all
  | uniform\s+(rotation|angle|parameter)
)""", re.I | re.X)

TASK_PAIRS = re.compile(r"""(
    28\s*(-|\s)?\s*(binary\s+)?(features?|dimensional|pairwise|pair)
  | (features?|dataset)[^.]{0,60}(qubit\s+)?pairs
  | pairwise\s+features?
  | all[- ]pairs\s+(feature|encoding|representation)
  | IsingZZ[^.]{0,40}(all[- ]to[- ]all|complete|every pair|graph)
  | FEATURE_PAIRS
)""", re.I | re.X)

PARTIAL = re.compile(r"""(
    mirror\w* | parity | even/odd | even[- ]odd | reflect\w*
  | pair[- ](tied|shared|sharing|symmetr\w*)
  | quadrant | bipartite | mod[- ]?3
  | cyclic | translation\w*\s+(symmetr\w*|invarian\w*)
  | symmetric\s+(pairs?|qubit pairs)
)""", re.I | re.X)

BREAK = re.compile(r"""(
    break\w*\s+(the\s+|this\s+|full\s+|strict\s+|permutation\s+|its\s+)*symmetr\w*
  | break\w*\s+(the\s+)?(full\s+)?permutation
  | symmetry[- ]breaking
  | relax\w*\s+(the\s+)?(strict\s+|full\s+)?symmetr\w*
  | (too|overly)\s+(restrictive|symmetric)
  | de[- ]?symmetri\w*
)""", re.I | re.X)

# words that turn a mention into a rejection when they sit just before it
NEG = re.compile(r"(avoid\w*|instead\s+of|rather\s+than|without|forgo\w*|eschew\w*|"
                 r"not\s+use|no\s+need\s+for|unlike|characteristic\s+of|"
                 r"replaces?\s+the|drop\w*|remove\w*|abandon\w*|limit\w*|better\s+than|rather\s+then|compared\s+to|than)[\w\s,\u2013-]{0,32}$", re.I)


def positive(pat, text, window=70):
    """True if the pattern fires at least once outside a rejection context."""
    for m in pat.finditer(text):
        if not NEG.search(text[max(0, m.start() - window):m.start()]):
            return True
    return False


FEATMAP = re.compile(r"(feature[- ]map|IsingZZ|the (28|binary|pair(wise)?) features?|"
                     r"features? (are|is) encoded|data[- ]encoding|encodes? \d* ?features?|"
                     r"dataset('s)? features?|feature[- ]pair)", re.I)


def build_claim(text):
    """True if some un-negated all-pairs / permutation mention is about the
    circuit being proposed rather than about the fixed feature map."""
    for pat in (PERM, ALLPAIRS):
        for m in pat.finditer(text):
            left = text[max(0, m.start() - 70):m.start()]
            if NEG.search(left):
                continue
            if FEATMAP.search(text[max(0, m.start() - 90):m.end() + 90]):
                continue
            return True
    return False


def label_note(name, desc):
    text = ((name or "").replace("_", " ") + " . " + (desc or "")).strip()
    f = set()
    if positive(PERM, text):
        f.add("names_perm")
    if positive(ALLPAIRS, text):
        f.add("all_pairs")
    if positive(COLLECTIVE, text):
        f.add("collective")
    if positive(TASK_PAIRS, text):
        f.add("task_pairs")
    if PARTIAL.search(text):
        f.add("partial_sym")
    if BREAK.search(text):
        f.add("breaks_sym")
    if not f:
        f.add("none")
    return {
        "flags": sorted(f),
        "claims": bool({"names_perm", "all_pairs"} & f),
        "build_claim": bool({"names_perm", "all_pairs"} & f) and build_claim(text),
        "hints": bool({"names_perm", "all_pairs", "collective", "task_pairs"} & f),
        "chars": len(text),
    }


def union_pairs(code):
    """Distinct unordered 2-qubit pairs touched anywhere in the ansatz block.

    A frontier trick is to split the complete graph into two or three stages
    separated by mixers; no single layer then covers all 28 pairs even though
    the block does.  This counts the block as a whole.
    """
    gates = norm(extract_spec(code) or [])
    if not gates:
        return None
    return len({frozenset(g["wires"]) for g in gates if g["kind"] == "2q"})


def main():
    by_pid = {}
    for fpath in sorted(glob.glob(os.path.join(ROOT, "viz/data/run_sn-transfer-*.js"))):
        rid = os.path.basename(fpath)[4:-3]
        if not classify(rid):
            continue
        for p in load_run(fpath)["programs"]:
            by_pid[(rid, p["id"])] = {
                "patch_name": p.get("patch_name"),
                "patch_description": p.get("patch_description") or "",
                "union_pairs": union_pairs(p.get("code")),
                **label_note(p.get("patch_name"), p.get("patch_description")),
            }
    rows = json.load(open(os.path.join(ROOT, "labelling/labels.json")))
    out = []
    for r in rows:
        n = by_pid.get((r["run_id"], r["program_id"]))
        if n is None:
            continue
        out.append({**r, "note": n})
    json.dump(out, open(os.path.join(ROOT, "labelling/note_labels.json"), "w"))
    from collections import Counter
    c = Counter(fl for r in out if r["own"] for fl in r["note"]["flags"])
    print("programs:", len(out), "own:", sum(r["own"] for r in out))
    for k, v in c.most_common():
        print(f"  {k:12s} {v}")


if __name__ == "__main__":
    main()
