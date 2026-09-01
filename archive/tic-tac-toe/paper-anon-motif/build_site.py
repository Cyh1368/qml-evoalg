"""Assemble the standalone tabbed site: overview plus one tab per task.

The organising principle is the variant ladder. Each task was run under two or
three information conditions that differ only in what the proposer was told, and
the site's job is to make that difference impossible to miss: every tab leads
with the ladder, states what was added or removed at each rung, and puts the
outcome of each rung next to it.

Figures are inlined as base64 data URIs so the file works offline.
"""
import base64
import html
import json
import re
from pathlib import Path

SP = Path(__file__).resolve().parent
OUT = SP / "site.html"

FIG_NAMES = [
    "fig_task", "fig_anonymize", "fig_strata", "fig_circuits", "fig_trajectory",
    "fig_summary", "fig_vocab", "fig_recall", "fig_symmetry", "fig_zerocontext",
    "fig_zc_motif", "fig_spin", "fig_deflate",
]


def img(name):
    b64 = base64.b64encode((SP / f"{name}.png").read_bytes()).decode()
    return f"data:image/png;base64,{b64}"


FIGS = {n: img(n) for n in FIG_NAMES}

_raw = (SP / "prompts.txt").read_text()
PROMPTS = {}
for _tag in ("MOTIF", "SN", "SU2"):
    _m = re.search(r"<<<<<<<<<<%s\n(.*?)\n>>>>>>>>>>%s" % (_tag, _tag), _raw, re.S)
    PROMPTS[_tag] = html.escape(_m.group(1).strip("\n")) if _m else "(missing)"
PROMPTS["LEAKY"] = html.escape((SP / "leaky_seed.txt").read_text().strip("\n"))

# The zero-context task message and seed, quoted from the built task so the site
# and the cluster runs cannot drift apart.
PROMPTS["ZC"] = html.escape("""You are optimizing a parametrized quantum circuit.

Goal:
Evolve the ANSATZ_SPEC below. Fixed code trains each candidate and returns
numeric feedback. You are NOT told what the data is, what the inputs represent,
what the labels mean, or how the inputs are encoded into the circuit, and you do
not need to know any of it. Your only guide is the feedback you receive.

Fixed architecture:
- 8 qubits, indexed 0..7.
- The input encoding, the readout, the training loop and the metrics are fixed
  and are implemented outside this file.
- The candidate ansatz block is applied a fixed number of times, with
  independent parameter copies per repetition.

Only edit the EVOLVE-BLOCK, that is ANSATZ_SPEC. Nothing else is editable.

Formal ANSATZ_SPEC schema:
- Single-qubit parametrized gates:
  {"gate": "RX"|"RY"|"RZ", "wire": int 0..7, "param": "name"}
- Fixed two-qubit gates:
  {"gate": "CNOT"|"CZ", "wires": [first, second]}
- Parametrized controlled rotations:
  {"gate": "CRX"|"CRY"|"CRZ", "wires": [control, target], "param": "name"}

Two-qubit gates may act on ANY pair of distinct qubits.

Parameter sharing:
Reusing the same param string shares that parameter within one ansatz block.
Use sharing deliberately: it is the only way to reduce the parameter count
without removing gates.

Candidate quality:
Improve validation accuracy, reduce the train-test gap, reduce
L2 loss, use parameters efficiently, and converge in fewer steps.

Invalid candidates are rejected for unsupported gates, bad wires, non-finite
metrics, or too many parameters.""")

PROMPTS["HINT_SEED"] = html.escape('''"""Seed program for ShinkaEvolve ansatz search: 8-qubit binary classifier.

Records are 28-dimensional binary feature vectors from an external dataset.
Each feature k is encoded by the fixed feature map as a two-qubit phase
coupling on the qubit pair FEATURE_PAIRS[k]. Labels are +1/-1 and encode a
property of the records determined by the dataset.
"""''')

PROMPTS["ZC_SEED"] = html.escape('''"""Seed program. Only ANSATZ_SPEC inside the EVOLVE-BLOCK is evolved.

Everything else about the task, that is how inputs are encoded, how the circuit
is measured, how training works and how metrics are computed, is fixed and lives
in a module that is not reproduced here. No information about the data is
available in this file.
"""''')

CSS = """
:root {
  --paper:#fbfbf9; --ink:#12140f; --muted:#63675f; --rule:#e2e4dd;
  --plate:#ffffff; --band:#f2f3ee; --raise:#ffffff;
  --win:#1b7837; --off:#c2453a; --hid:#7b3294; --warn:#b06d00;
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,"Times New Roman",serif;
  --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: dark) {
  :root {
    --paper:#101210; --ink:#e9eae4; --muted:#9aa096; --rule:#2a2d28;
    --plate:#f7f7f4; --band:#181b18; --raise:#171a17;
    --win:#4faf73; --off:#e0736a; --hid:#b07fd0; --warn:#d9a441;
  }
}
:root[data-theme="dark"] {
  --paper:#101210; --ink:#e9eae4; --muted:#9aa096; --rule:#2a2d28;
  --plate:#f7f7f4; --band:#181b18; --raise:#171a17;
  --win:#4faf73; --off:#e0736a; --hid:#b07fd0; --warn:#d9a441;
}
:root[data-theme="light"] {
  --paper:#fbfbf9; --ink:#12140f; --muted:#63675f; --rule:#e2e4dd;
  --plate:#ffffff; --band:#f2f3ee; --raise:#ffffff;
  --win:#1b7837; --off:#c2453a; --hid:#7b3294; --warn:#b06d00;
}

* { box-sizing:border-box; }
html { scroll-padding-top:66px; }
[id] { scroll-margin-top:66px; }
body {
  background:var(--paper); color:var(--ink);
  font-family:var(--serif); font-size:17px; line-height:1.62;
  margin:0; padding:0 20px 96px; -webkit-font-smoothing:antialiased;
}
/* Centre horizontally with longhands only. The `margin` shorthand here would
   outrank the element rules below (class beats type) and flatten every vertical
   margin on .wrap/.wide headings and figures. */
.wrap { max-width:68ch; margin-left:auto; margin-right:auto; }
.wide { max-width:1000px; margin-left:auto; margin-right:auto; }

/* ---------------------------------------------------------------- nav */
.topbar {
  position:sticky; top:0; z-index:50; background:var(--paper);
  border-bottom:1px solid var(--rule); margin:0 -20px 0; padding:0 20px;
  backdrop-filter:saturate(180%) blur(8px);
}
.topbar .inner {
  max-width:1000px; margin:0 auto; display:flex; align-items:center;
  gap:18px; flex-wrap:wrap; padding:11px 0;
}
.brand {
  font-family:var(--sans); font-size:12.5px; font-weight:600;
  letter-spacing:.11em; text-transform:uppercase; color:var(--ink);
  margin-right:auto; white-space:nowrap;
}
nav.tabs { display:flex; gap:4px; flex-wrap:wrap; }
nav.tabs button {
  font-family:var(--sans); font-size:13.5px; color:var(--muted);
  background:none; border:1px solid transparent; border-radius:999px;
  padding:5px 13px; cursor:pointer; white-space:nowrap;
}
nav.tabs button:hover { color:var(--ink); background:var(--band); }
nav.tabs button[aria-selected="true"] {
  color:var(--paper); background:var(--ink); border-color:var(--ink);
}
nav.tabs button .q {
  font-family:var(--mono); font-size:11px; opacity:.62; margin-right:5px;
}

section.tab { display:none; }
section.tab.active { display:block; animation:fade .18s ease-out; }
@keyframes fade { from { opacity:0; transform:translateY(3px);} to {opacity:1;} }

/* ---------------------------------------------------------------- text */
header.page { padding:72px 0 6px; }
h1 { font-size:clamp(29px,5vw,42px); line-height:1.1; font-weight:600;
     margin:0 0 14px; letter-spacing:-.015em; text-wrap:balance; }
.dek { font-size:19px; color:var(--muted); margin:0 0 20px; text-wrap:balance; }
.byline { font-family:var(--sans); font-size:12px; letter-spacing:.09em;
          text-transform:uppercase; color:var(--muted);
          border-top:1px solid var(--rule); padding-top:14px; }
h2 { font-family:var(--sans); font-size:12.5px; font-weight:600;
     letter-spacing:.13em; text-transform:uppercase; color:var(--muted);
     margin:56px 0 14px; padding-bottom:8px; border-bottom:1px solid var(--rule); }
h3 { font-size:20px; font-weight:600; margin:32px 0 8px; letter-spacing:-.01em; }
p { margin:0 0 16px; }
code { font-family:var(--mono); font-size:.85em; background:var(--band);
       padding:.12em .34em; border-radius:2px; }
a { color:var(--hid); text-decoration:underline; text-underline-offset:2px; }
a.taskcard { text-decoration:none; }
.note { font-size:15px; color:var(--muted); border-left:2px solid var(--rule);
        padding-left:18px; margin:24px 0; }

/* ------------------------------------------------------- variant ladder */
.ladder { display:grid; gap:16px; margin:30px 0 8px; }
@media (min-width:860px) { .ladder.three { grid-template-columns:repeat(3,1fr); }
                           .ladder.two { grid-template-columns:repeat(2,1fr); } }
.rung {
  background:var(--raise); border:1px solid var(--rule);
  border-top:3px solid var(--edge, var(--muted));
  padding:18px 18px 16px; display:flex; flex-direction:column;
}
.rung.given  { --edge:var(--off); }
.rung.part   { --edge:var(--warn); }
.rung.none   { --edge:var(--win); }
.rung .step {
  font-family:var(--mono); font-size:11px; letter-spacing:.08em;
  text-transform:uppercase; color:var(--muted); margin-bottom:4px;
}
.rung h4 { font-size:18px; margin:0 0 4px; font-weight:600; letter-spacing:-.01em; }
.rung .meta {
  font-family:var(--sans); font-size:12.5px; color:var(--muted);
  margin:0 0 12px; padding-bottom:11px; border-bottom:1px solid var(--rule);
}
.chips { list-style:none; margin:0 0 14px; padding:0; display:grid; gap:7px; }
/* Absolute marker, not a grid column: inline children such as <code> must stay
   in the text flow instead of becoming grid items of their own. */
.chips li {
  font-family:var(--sans); font-size:13.2px; line-height:1.45;
  position:relative; padding-left:20px;
}
.chips li::before {
  position:absolute; left:2px; top:0;
  font-family:var(--mono); font-weight:700; line-height:1.45;
}
.chips li code { font-size:.86em; white-space:nowrap; }
.chips li.yes::before { content:"+"; color:var(--off); }
.chips li.no::before  { content:"\\2013"; color:var(--muted); }
.chips li.no { color:var(--muted); }
.rung .outcome { margin-top:auto; padding-top:12px; border-top:1px solid var(--rule); }
.rung .outcome .lab {
  font-family:var(--sans); font-size:11px; letter-spacing:.1em;
  text-transform:uppercase; color:var(--muted); display:block; margin-bottom:3px;
}
.rung .outcome .big {
  font-family:var(--mono); font-size:24px; letter-spacing:-.02em;
  font-variant-numeric:tabular-nums; display:block; line-height:1.2;
}
.rung .outcome .big.multi { font-size:16.5px; letter-spacing:0; }
.rung .outcome .sub { font-family:var(--sans); font-size:13px; color:var(--muted); }
/* the decisive test, shown on every rung so the three are comparable at a glance */
.rung .outcome .also {
  display:block; margin-top:10px; padding-top:9px;
  border-top:1px dotted var(--rule);
  font-family:var(--sans); font-size:12.8px; color:var(--muted);
}
.rung .outcome .also b { font-family:var(--mono); font-size:13.5px; }
.rung .outcome .also b.win { color:var(--win); }
.rung .outcome .also b.off { color:var(--off); }
.big.win { color:var(--win); } .big.off { color:var(--off); } .big.warn { color:var(--warn); }

/* the single changed line, shown as a diff */
.diff { border:1px solid var(--rule); margin:26px 0; background:var(--raise); }
.diff .hd {
  font-family:var(--sans); font-size:12px; letter-spacing:.09em;
  text-transform:uppercase; color:var(--muted);
  padding:10px 14px; border-bottom:1px solid var(--rule);
}
.diff pre {
  font-family:var(--mono); font-size:12.4px; line-height:1.55; margin:0;
  padding:12px 14px; overflow-x:auto; white-space:pre-wrap; word-break:break-word;
}
.diff pre.minus { background:color-mix(in srgb, var(--off) 11%, transparent);
                  border-left:3px solid var(--off); }
.diff pre.plus  { background:color-mix(in srgb, var(--win) 11%, transparent);
                  border-left:3px solid var(--win); }

/* ------------------------------------------------------------- figures */
figure { margin:32px 0; }
.plate { background:var(--plate); border:1px solid var(--rule); padding:14px;
         overflow-x:auto; }
.plate img { display:block; width:100%; height:auto; min-width:520px; }
figcaption { font-family:var(--sans); font-size:13px; line-height:1.5;
             color:var(--muted); margin-top:10px; }

/* -------------------------------------------------------------- tables */
.tablewrap { overflow-x:auto; margin:26px 0; }
table { border-collapse:collapse; width:100%; min-width:560px; font-size:15px; }
th, td { text-align:right; padding:9px 12px; border-bottom:1px solid var(--rule);
         font-variant-numeric:tabular-nums; }
th:first-child, td:first-child { text-align:left; font-family:var(--sans); font-size:13.5px; }
thead th { font-family:var(--sans); font-size:12px; font-weight:600;
           letter-spacing:.05em; color:var(--muted); border-bottom:1.5px solid var(--ink); }
thead th.grp { text-align:center; border-bottom:1px solid var(--rule); }
tbody tr.key td { background:color-mix(in srgb, var(--band) 70%, transparent); font-weight:600; }
td.win { color:var(--win); font-weight:600; }
td.off { color:var(--off); font-weight:600; }
.mono { font-family:var(--mono); font-size:.92em; }
.vrule { border-left:1px solid var(--rule); }

/* ------------------------------------------------------------ verdicts */
.verdict { border:1px solid var(--rule); border-left:3px solid var(--edge,var(--ink));
           background:var(--raise); padding:18px 20px; margin:30px 0; }
.verdict.fail { --edge:var(--off); } .verdict.pass { --edge:var(--win); }
.verdict .lab { font-family:var(--sans); font-size:11px; letter-spacing:.11em;
                text-transform:uppercase; color:var(--muted); display:block; margin-bottom:6px; }
.verdict p:last-child { margin-bottom:0; }

blockquote { margin:20px 0; padding:2px 0 2px 20px; border-left:2px solid var(--hid);
             font-style:italic; }
blockquote cite { display:block; font-style:normal; font-family:var(--sans);
                  font-size:12.5px; letter-spacing:.04em; color:var(--muted); margin-top:8px; }

details.prompt { border-top:1px solid var(--rule); padding:14px 0; }
details.prompt:last-of-type { border-bottom:1px solid var(--rule); }
details.prompt > summary { cursor:pointer; list-style:none; font-family:var(--sans);
                           font-size:14px; display:flex; align-items:baseline; gap:10px; }
details.prompt > summary::-webkit-details-marker { display:none; }
details.prompt > summary::before { content:"+"; font-family:var(--mono); color:var(--muted); }
details.prompt[open] > summary::before { content:"\\2212"; }
details.prompt .tag { font-size:11.5px; letter-spacing:.08em; text-transform:uppercase;
                      color:var(--muted); margin-left:auto; }
details.prompt pre { font-family:var(--mono); font-size:12px; line-height:1.5;
                     background:var(--band); padding:14px 16px; margin:12px 0 0;
                     overflow-x:auto; white-space:pre; border-left:2px solid var(--rule); }
details.prompt.leak pre { border-left-color:var(--off); }

/* --------------------------------------------------------- task cards */
.taskgrid { display:grid; gap:16px; margin:26px 0; }
@media (min-width:820px) { .taskgrid { grid-template-columns:repeat(3,1fr); } }
a.taskcard {
  display:block; text-decoration:none; color:inherit; background:var(--raise);
  border:1px solid var(--rule); padding:18px; cursor:pointer;
}
a.taskcard:hover { border-color:var(--ink); }
a.taskcard .q { font-family:var(--mono); font-size:11px; letter-spacing:.09em;
                text-transform:uppercase; color:var(--muted); }
a.taskcard h4 { font-size:18px; margin:5px 0 6px; font-weight:600; }
a.taskcard p { font-size:14.5px; line-height:1.5; color:var(--muted); margin:0 0 12px; }
a.taskcard .status { font-family:var(--sans); font-size:12.5px; font-weight:600; }
a.taskcard .status.fail { color:var(--off); }
a.taskcard .status.pass { color:var(--win); }

footer { margin-top:64px; padding-top:18px; border-top:1px solid var(--rule);
         font-family:var(--sans); font-size:13px; color:var(--muted); }
"""

# ------------------------------------------------------------------ overview
OVERVIEW = """
<header class="page wrap">
  <h1>Discovery or recall?</h1>
  <p class="dek">Three ansatz-search tasks, each run under several information
  conditions. Every condition changes only what the model was told. Twice, a
  result that looked like discovery turned out to belong to a single sentence.</p>
  <p class="byline">Cheng-You Ho &nbsp;·&nbsp; Yale Quantum Institute &nbsp;·&nbsp; ShinkaEvolve on Bouchet</p>
</header>

<div class="wrap">
  <p>Evolutionary search driven by a large language model is often reported to
  <em>discover</em> the structure of a problem. Two very different things produce
  that claim. A system that rediscovers structure it was shown is a search
  procedure with a good prior. A system that finds structure nobody supplied is
  something else entirely.</p>

  <p>Telling them apart requires knowing exactly what the model was shown, and
  that accounting is usually missing. So we built each task in several variants
  that are identical in data, reward and budget, and differ only in what the
  instructions and the starter file say. Then we removed information and reran.</p>

  <p>We had a result of the first kind and mistook it for the second. Twice.</p>
</div>

<h2 class="wrap">The three tasks</h2>
<div class="wide taskgrid">
  <a class="taskcard" data-goto="ttt">
    <span class="q">Task 1 &nbsp;·&nbsp; 9 qubits</span>
    <h4>Tic-tac-toe</h4>
    <p>Classify a board position. The structure that matters is the eight winning
    lines, out of 84 possible qubit triples.</p>
    <span class="status fail">3 variants &nbsp;·&nbsp; never discovered</span>
  </a>
  <a class="taskcard" data-goto="graph">
    <span class="q">Task 2 &nbsp;·&nbsp; 8 qubits</span>
    <h4>Graph connectedness</h4>
    <p>Classify networks on eight nodes. The structure that matters is
    permutation symmetry: renaming nodes cannot change the label.</p>
    <span class="status fail">2 variants &nbsp;·&nbsp; found only when told</span>
  </a>
  <a class="taskcard" data-goto="spin">
    <span class="q">Task 3 &nbsp;·&nbsp; 8 qubits</span>
    <h4>Spin states</h4>
    <p>Classify quantum states of a spin ring. The structure that matters is the
    rotationally invariant coupling.</p>
    <span class="status fail">2 variants &nbsp;·&nbsp; task measures nothing</span>
  </a>
</div>

<h2 class="wrap">What the variants are for</h2>
<div class="wrap">
  <p>Each task has a <strong>ladder</strong>. At the top rung the model is handed
  the answer or the premise it follows from. At the bottom rung it is told
  essentially nothing: the qubit count, the legal gates, and a number after every
  attempt. Rungs in between remove one thing at a time.</p>

  <p>The point of the ladder is that a successful run is uninterpretable on its
  own. A derivation from a leaked premise and a genuine discovery look identical
  in the trace, because in both cases the model writes down a correct piece of
  structure and the score rewards it. The only way to separate them is to delete
  something and see whether the result survives.</p>

  <p class="note">One detail governs everything. ShinkaEvolve puts the entire
  starter file into the prompt at every generation, so sanitising the
  instructions is not enough. Both of our leaks came through the starter file,
  and the second one got past us because it read like a routine encoding note
  rather than like an answer.</p>
</div>

<h2 class="wrap">What we found</h2>
<div class="wrap">
  <p><strong>The motif was never discovered.</strong> Given the winning lines,
  the search used them in every circuit. With the lines hidden behind a secret
  relabelling, usage collapsed, and running four times longer with no context at
  all made it worse rather than better. No variant ever found the two lines that
  can only be reached from the score.</p>

  <p><strong>The symmetry was discovered only when the premise was stated.</strong>
  Told that the 28 features are the pairs of eight qubits, GPT-5.6-sol deduced
  permutation invariance at generation 33 and gained six points of test accuracy.
  Delete that one sentence, change nothing else, and no model builds an
  equivariant circuit in 80 generations.</p>

  <p><strong>The spin task measures nothing.</strong> The fixed encoder already
  solves it, so the circuit is irrelevant, and an attempt to fix that by
  rewarding parameter economy made the empty circuit optimal.</p>

  <p>What survives is narrower than discovery: these systems carry a stated
  premise one deductive step into a design, and measurement corrects them when
  the step is wrong. That is useful. It is not a scientific instrument.</p>
</div>

<h2 class="wrap">Method</h2>
<div class="wrap">
  <p>ShinkaEvolve proposes an edit to a circuit specification; the fixed
  pipeline trains and scores it; higher-scoring circuits are more likely to be
  chosen as parents. One generation is one proposed circuit, evaluated. Only the
  <code>ANSATZ_SPEC</code> block is searched: the data, encoding, training loop
  and readout are frozen, so every candidate is compared on the same task.</p>

  <p>Each arm uses a single proposer model, so the arms within a variant are
  matched to each other. Runs are on the Yale Bouchet cluster, one SLURM job per
  evaluation. The relabelling that hides the winning lines uses a fixed secret
  permutation, seed 777.</p>
</div>
"""

# ------------------------------------------------------------------ task: ttt
TTT = """
<header class="page wrap">
  <h1>Tic-tac-toe</h1>
  <p class="dek">Nine qubits, 84 possible triples, eight of which decide the
  answer. Three variants, each removing more of what the model was told.</p>
  <p class="byline">Task 1 &nbsp;·&nbsp; the motif is a convention, not a symmetry</p>
</header>

<div class="wrap">
  <p>Classify a board position into one of three outcomes. The nine cells become
  nine qubits, and the search rewrites a circuit that reads them. It may join any
  three qubits with a three-qubit gate. The three rows, three columns and two
  diagonals are the <strong>winning lines</strong>, and they alone determine the
  answer. A search that puts its gates there has found the real structure.</p>
</div>

<figure class="wide">
  <div class="plate"><img src="{fig_task}" alt="Board cells mapped to nine qubits, the eight winning lines, and the hardware connectivity."></div>
  <figcaption class="wrap" style="margin:10px auto 0;">The nine cells become nine
  qubits (a). The eight winning lines (b). The twelve qubit pairs the hardware
  permits (c).</figcaption>
</figure>

<h2 class="wrap">What the search may write</h2>
<div class="wrap">
  <p>The model edits exactly one thing: a Python list named
  <code>ANSATZ_SPEC</code>, read out gate by gate to build the circuit. The input
  encoding, the readout, the training loop and the metrics are fixed, and in the
  later rungs live in a module the model never sees. Each entry of the list draws
  from a closed menu:</p>
</div>

<div class="wide tablewrap">
  <table>
    <thead>
      <tr><th>Gates</th><th>Acts on</th><th>Parametrized</th><th>Where it may go</th></tr>
    </thead>
    <tbody>
      <tr><td><code>RX</code>, <code>RY</code>, <code>RZ</code></td><td>1 qubit</td><td>yes</td><td>any of the nine qubits</td></tr>
      <tr><td><code>CNOT</code>, <code>CZ</code></td><td>2 qubits</td><td>no</td><td>only the twelve hardware pairs</td></tr>
      <tr><td><code>CRX</code>, <code>CRY</code>, <code>CRZ</code></td><td>2 qubits</td><td>yes</td><td>only the twelve hardware pairs</td></tr>
      <tr class="key"><td><code>ZZZ</code>, <code>CCRZ</code></td><td>3 qubits</td><td>yes</td><td><strong>any</strong> of the 84 triples, no restriction</td></tr>
    </tbody>
  </table>
</div>

<div class="wrap">
  <p>Parameters are named strings; reusing a name shares the parameter, which is
  the only way to cut the parameter count without deleting gates. A candidate is
  rejected outright for an unsupported gate, a wire outside 0..8, a two-qubit
  gate off the hardware graph, a non-finite metric, or too many parameters.
  Everything else is trained and scored.</p>
  <p>The asymmetry in the last row is deliberate. Two-qubit gates are pinned to
  the hardware graph, so nothing two-qubit can express a preference the wiring
  does not already suggest. The three-qubit vocabulary is free: 84 possible
  triples, eight of which are winning lines. Where a model puts its three-qubit
  gates is therefore the cleanest record of what it believes about the
  problem.</p>
</div>

<h2 class="wrap">The three variants</h2>
<div class="wrap">
  <p>Each rung removes one channel through which the answer could reach the
  model. The data and the reward are the same throughout; the winning lines stay
  exactly as predictive.</p>
</div>

<div class="wide ladder three">
  <div class="rung given">
    <span class="step">Rung 1</span>
    <h4>Answer given</h4>
    <p class="meta">100 generations · bandit over Haiku 4.5, GPT-5-mini, Gemini 3 Flash</p>
    <ul class="chips">
      <li class="yes">Starter file defines <code>WIN_LINES</code>, <code>CORNERS</code>, <code>CENTER</code></li>
      <li class="yes">ASCII diagram of the board</li>
      <li class="yes">Instructions name tic-tac-toe three times</li>
      <li class="yes">Board labelling is the standard one</li>
    </ul>
    <div class="outcome">
      <span class="lab">Gates on winning lines</span>
      <span class="big off">916 / 916</span>
      <span class="sub">Every gate, no exploratory error. All eight lines by generation 5.</span>
      <span class="also">Decisive test: <b class="win">2 / 2</b> hidden lines found</span>
    </div>
  </div>

  <div class="rung part">
    <span class="step">Rung 2</span>
    <h4>Anonymised</h4>
    <p class="meta">30 generations · Haiku 4.5, Sonnet 5, GPT-5.6-sol separately</p>
    <ul class="chips">
      <li class="no">No <code>WIN_LINES</code>, no geometric constants, no diagram</li>
      <li class="no">Game never named; described as nine inputs, three classes</li>
      <li class="yes">Secret permutation of the nine qubit labels</li>
      <li class="yes">Starter file still contains the pipeline</li>
    </ul>
    <div class="outcome">
      <span class="lab">Gates on winning lines</span>
      <span class="big warn multi">35/89 &middot; 0/46 &middot; 7/95</span>
      <span class="sub">39%, 0%, 7.4%. Three models, three different answers; the
      last is below chance.</span>
      <span class="also">Decisive test: <b class="off">0 / 2</b> hidden lines found</span>
    </div>
  </div>

  <div class="rung none">
    <span class="step">Rung 3</span>
    <h4>Zero context</h4>
    <p class="meta">80 generations · Haiku 4.5, Sonnet 5, GPT-5.6-sol separately</p>
    <ul class="chips">
      <li class="no">Nothing about the data, the labels or the encoding</li>
      <li class="no">Whole pipeline moved into an unshown module</li>
      <li class="no">Scoring formula never shown</li>
      <li class="yes">Qubit count, legal gates, and a number after each attempt</li>
    </ul>
    <div class="outcome">
      <span class="lab">Gates on winning lines</span>
      <span class="big multi">1/180 &middot; 3/52 &middot; 12/18</span>
      <span class="sub">0.6%, 5.8%, 67%. Read the denominators: the 67% is 18 gates,
      and it does not survive <a href="#deflate">a closer look</a>.</span>
      <span class="also">Decisive test: <b class="off">0 / 2</b> hidden lines found</span>
    </div>
  </div>
</div>

<div class="wrap">
  <p class="note">The 67% looks like a discovery and is not one. Seven of that
  arm's twelve on-line gates are a single triple inherited down a lineage, and
  that triple is the one coincidence between the true relabelled lines and the
  lines of an ordinary board. Counted once per distinct triple it is 3 of 7,
  which is not significant. The rising order across the three arms is not a
  capability ranking either: it reverses on fitness, on accuracy, and on the
  second zero-context task. <a href="#ranking">Is it a capability ranking?</a></p>
</div>

<h2 class="wrap">Why the relabelling is the whole design</h2>
<div class="wrap">
  <p>Under a secret permutation the winning lines stay exactly as predictive, but
  they are no longer rows or columns of anything the model can see. A model
  recalling the game will place gates on the lines it remembers, which are now
  wrong. Prior knowledge fails <em>visibly</em> rather than being merely absent.</p>
</div>

<figure class="wide">
  <div class="plate"><img src="{fig_anonymize}" alt="The eight winning lines before and after the secret relabelling."></div>
  <figcaption class="wrap" style="margin:10px auto 0;">The same eight lines before
  and after relabelling. Obvious geometry becomes a scatter. Purple marks the two
  lines with no hardware link, reachable only from the score.</figcaption>
</figure>

<h2 class="wrap">How the qubits are scrambled</h2>
<div class="wrap">
  <p>The relabelling is one uniform random permutation of the nine labels, drawn
  once when the task data is built (a seeded NumPy generator, so the build is
  reproducible), and then frozen. Cell <i>c</i> of the board is encoded on qubit
  &pi;(<i>c</i>): the dataset's columns are reordered once and written to disk,
  the twelve hardware edges and the readout wiring are mapped through the same
  permutation, and the eight winning lines land wherever &pi; sends them. Every
  candidate, every generation and every proposer model then sees the same fixed
  labelling, in both the anonymised and zero-context rungs.</p>
  <p>Freezing it is the point. Re-drawing the permutation per sample or per
  generation would leave nothing stable to discover. Holding it fixed keeps the
  winning lines exactly as predictive as they ever were, so a persistent search
  could in principle recover them from the score alone. The permutation itself
  is stored in a metadata file that exists only on the analysis side; no channel
  the model sees contains it.</p>
</div>

<h2 class="wrap">The two hidden lines, and how a hit is counted</h2>
<div class="wrap">
  <p>A winning line is <strong>hidden</strong> when none of its three qubit
  pairs is a hardware edge. On the ordinary board these are the two diagonals:
  rows and columns each contain two grid-adjacent pairs, the diagonals contain
  none. After the relabelling they are the triples <code>(0,1,6)</code> and
  <code>(0,4,5)</code> in the model's coordinates. Nothing the model can see
  points at them. No two-qubit gate can sit on any of their pairs, they carry no
  connectivity signal, and the relabelling has severed them from any remembered
  geometry. The accuracy signal is the only path that leads to them, which is
  what makes them the decisive test: the other six lines can be hit by a mundane
  preference for well-connected triples, these two cannot.</p>
  <p>Counting a hit is mechanical. Every program that compiles is parsed, its
  <code>ANSATZ_SPEC</code> is read back, and each three-qubit gate contributes
  the unordered triple of qubits it acts on. A triple is on a line when it
  equals one of the eight true triples recorded in the secret metadata file,
  as a set, exactly; a near miss sharing two of three qubits counts for
  nothing. A <em>hidden-line find</em> means some program placed a three-qubit
  gate exactly on <code>(0,1,6)</code> or <code>(0,4,5)</code>. The run handed
  the answer found both within five generations. Across every anonymised and
  zero-context arm, over up to 80 generations and hundreds of programs, neither
  was ever hit.</p>
  <p class="note">Raw gate counts overstate the evidence, because a child
  program inherits its parent's gates; <a href="#deflate">the deflation
  section</a> counts each distinct triple once per run before testing
  significance.</p>
</div>

<h2 class="wrap">What should count as chance</h2>
<div class="wrap">
  <p>Random placement hits a winning line 8/84 = 9.5% of the time. That baseline
  is wrong. Because the wiring is grid adjacency, six of the eight winning lines
  are exactly the triples carrying two hardware links, so a model that merely
  prefers well-connected qubits hits a line 27.3% of the time with no insight at
  all.</p>
</div>

<figure class="wide">
  <div class="plate"><img src="{fig_strata}" alt="Triples grouped by hardware links, showing six of eight winning lines in the two-link group."></div>
  <figcaption class="wrap" style="margin:10px auto 0;">Six of the eight winning
  lines carry two hardware links. Every number below is reported against both
  baselines.</figcaption>
</figure>

<h2 class="wrap">Results, rungs 1 and 2</h2>
<div class="wide tablewrap">
  <table>
    <thead>
      <tr><th></th><th>Answer given</th><th class="vrule">Haiku 4.5</th><th>Sonnet 5</th><th>GPT-5.6-sol</th></tr>
    </thead>
    <tbody>
      <tr><td>Generations</td><td>100</td><td class="vrule">30</td><td>30</td><td>30</td></tr>
      <tr><td>Gates on winning lines</td><td>916/916</td><td class="vrule">35/89</td><td>0/46</td><td>7/95</td></tr>
      <tr><td>&nbsp;&nbsp;as a fraction</td><td>100%</td><td class="vrule">39%</td><td>0%</td><td>7.4%</td></tr>
      <tr><td>p vs uniform (9.5%)</td><td class="mono">~10<sup>-935</sup></td><td class="mono vrule">6.7e-14</td><td class="mono">1.00</td><td class="mono">0.81</td></tr>
      <tr><td>p vs connectivity (27.3%)</td><td class="mono">~10<sup>-517</sup></td><td class="mono vrule">9.1e-3</td><td class="mono">1.00</td><td class="mono">1.00</td></tr>
      <tr><td>Distinct lines found</td><td>8/8</td><td class="vrule">3/8</td><td>0/8</td><td>0/8</td></tr>
      <tr class="key"><td>Hidden lines found</td><td class="win">2/2</td><td class="off vrule">0/2</td><td class="off">0/2</td><td class="off">0/2</td></tr>
      <tr><td>Proposals naming the game</td><td>92%</td><td class="vrule">10%</td><td>27%</td><td>30%</td></tr>
      <tr><td>Best test accuracy</td><td>78.2%</td><td class="vrule">65.5%</td><td>65.7%</td><td><strong>77.8%</strong></td></tr>
    </tbody>
  </table>
</div>

<figure class="wide">
  <div class="plate"><img src="{fig_summary}" alt="Summary bars: gates on lines, coverage, and hidden lines found."></div>
  <figcaption class="wrap" style="margin:10px auto 0;">Only the run handed the
  answer passes the decisive test (c).</figcaption>
</figure>

<h2 class="wrap">Results, rung 3</h2>
<div class="wrap">
  <p>With every remaining channel closed and nearly three times the horizon of
  rung 2, motif usage fell rather than rose, and no best circuit used a winning
  line at all.</p>
</div>

<div class="wide tablewrap">
  <table>
    <thead>
      <tr><th></th><th>Haiku 4.5</th><th>Sonnet 5</th><th>GPT-5.6-sol</th></tr>
    </thead>
    <tbody>
      <tr><td>Generations</td><td>80</td><td>80</td><td>80</td></tr>
      <tr><td>Gates on winning lines</td><td>1/180</td><td>3/52</td><td>12/18</td></tr>
      <tr><td>&nbsp;&nbsp;of which the coincidence triple</td><td>1</td><td>1</td><td class="off">7</td></tr>
      <tr><td>Distinct triples on lines</td><td>1/13</td><td>2/24</td><td>3/7</td></tr>
      <tr><td>p vs connectivity, distinct</td><td class="mono">0.98</td><td class="mono">1.00</td><td class="mono">0.29</td></tr>
      <tr><td>Distinct lines found</td><td>1/8</td><td>2/8</td><td>3/8</td></tr>
      <tr class="key"><td>Hidden lines found</td><td class="off">0/2</td><td class="off">0/2</td><td class="off">0/2</td></tr>
      <tr><td>Lines in the best circuit</td><td>0/3</td><td>no triples</td><td>no triples</td></tr>
      <tr><td>Best test accuracy</td><td>64.2%</td><td>65.0%</td><td>62.3%</td></tr>
    </tbody>
  </table>
</div>

<figure class="wide">
  <div class="plate"><img src="{fig_zc_motif}" alt="Where the zero-context arms placed their gates, the deflated signal, and the hidden-line test."></div>
  <figcaption class="wrap" style="margin:10px auto 0;">(a) Every gate placed,
  classified by whether its triple is a true line, a line of an <em>unpermuted</em>
  board only, or neither. (b) The one positive signal, before and after counting
  inherited copies once. (c) The decisive test, unchanged.</figcaption>
</figure>

<div class="wrap">
  <p>Panel (a) separates the arms rather than uniting them. Haiku's most-used
  triple, 56 of its 180 placements, is the main diagonal of an ordinary
  row-major board, which the relabelling made wrong; 72 of its 180 placements
  sit on row-major lines and exactly 1 on a true line. That arm behaves like a
  standard board is being assumed. GPT-5.6-sol does not: 1 of its 7 distinct
  triples is a row-major line, none is a line of the ring-labelled board this
  task family actually used, and its other two on-line triples,
  <code>(0,7,8)</code> and <code>(5,6,7)</code>, are lines of no ordinary
  board at all.</p>
</div>

<h2 class="wrap" id="deflate">How to read the 67%</h2>
<div class="wrap">
  <p>The three numbers 0.6%, 5.8% and 67% look like a capability ranking, with
  the strongest model recovering most of the motif. They are not, and the ways
  they mislead are worth setting out, because they are the same ways any
  enrichment statistic over an evolutionary run can mislead.</p>

  <h3>What the number is</h3>
  <p>It is not a score and not a fraction of the eight lines. For every program
  in a run that compiled and trained, we parse its circuit specification, take
  every three-qubit gate, and read off the triple of qubits it acts on. Pool
  those across the whole run, then ask what share of them are one of the eight
  true relabelled lines:</p>
</div>

<div class="wide tablewrap">
  <table>
    <thead>
      <tr><th></th><th>Programs using<br><span style="font-weight:400">three-qubit gates</span></th>
      <th>Gates placed<br><span style="font-weight:400">denominator</span></th>
      <th>On a true line<br><span style="font-weight:400">numerator</span></th>
      <th>Share</th></tr>
    </thead>
    <tbody>
      <tr><td>Haiku 4.5</td><td>56 of 59</td><td>180</td><td>1</td><td>0.6%</td></tr>
      <tr><td>Sonnet 5</td><td>21 of 76</td><td>52</td><td>3</td><td>5.8%</td></tr>
      <tr><td>GPT-5.6-sol</td><td>14 of 73</td><td class="off">18</td><td>12</td><td class="off">67%</td></tr>
    </tbody>
  </table>
</div>

<div class="wrap">
  <h3>The denominator is something the model chooses</h3>
  <p>This is a precision, not a coverage. Haiku reached for three-qubit gates in
  almost every program it wrote and placed 180 of them. GPT-5.6-sol used them in
  14 programs out of 73 and placed 18. A model that places one gate, on a line,
  scores 100%.</p>
  <p>So the headline mostly says <em>GPT barely used the three-qubit vocabulary
  at all</em>. Whatever the 67% measures, it is measured over eighteen draws.</p>

  <h3>They are not eighteen independent draws</h3>
  <p>A child program inherits its parent's gates. If a parent carries a
  three-qubit gate on some triple and the child edits something else, that gate
  is counted again, and again, for as long as the lineage survives. The
  binomial test behind every p-value assumes independent placements; evolution
  guarantees the opposite by construction.</p>
  <p>GPT's twelve on-line placements are three decisions:
  <code>(2,4,6)</code> seven times, <code>(0,7,8)</code> three times,
  <code>(5,6,7)</code> twice. Counting each distinct triple once gives 3 of 7,
  which against the connectivity-matched baseline is <strong>p = 0.29</strong>.
  Haiku and Sonnet deflate to 1 of 13 and 2 of 24, at p = 0.98 and p = 1.00.
  Nothing is significant.</p>

  <h3>Seven of the twelve are one ambiguous triple</h3>
  <p>The triple <code>(2,4,6)</code> is the single overlap between the eight true
  relabelled lines and the eight winning lines of an ordinary row-major board. It
  therefore cannot be counted as clean evidence of search: a model that assumed
  a row-major board and reached for the anti-diagonal would land on it for free,
  without having learned anything. Seven of GPT's twelve on-line placements are
  that one triple.</p>

  <div class="note wrap" style="margin:14px 0;">
    <strong>Two board labellings are in play, and they disagree about
    <code>(2,4,6)</code>.</strong> The original task numbers its qubits around a
    ring with the centre at 8, the labelling drawn in figure (b) near the top of
    this page, whose lines are <code>(0,1,2) (0,4,8) (0,6,7) (1,5,8) (2,3,4)
    (2,6,8) (3,7,8) (4,5,6)</code>. <code>(2,4,6)</code> is <em>not</em> among
    them. The comparison above instead uses plain row-major numbering, the
    convention a model reconstructing "tic-tac-toe on nine qubits" from nothing
    would most naturally assume, and there <code>(2,4,6)</code> is the
    anti-diagonal. Against the ring labelling the true relabelled lines overlap
    it in nothing at all, so under that reference the coincidence disappears and
    GPT's three on-line triples are all unexplained. Row-major is the harder
    test of the two and is the one reported.
  </div>

  <p>What the run does <em>not</em> show is any sign that recall is driving the
  choice. Across all three zero-context arms, <strong>no proposal mentions
  tic-tac-toe, a board, cells, or winning lines</strong>: the strict rate is 0 of
  80, 0 of 79 and 0 of 80. GPT's stated reason for putting a gate there is
  entirely structural, and never names the game:</p>
  <blockquote>
    Add one parametrized ZZZ interaction before the CZ layer to model
    higher-order correlations among qubits 2, 4 and 6.
    <cite>GPT-5.6-sol, generation 19, <code>add_zzz_correlation_probe</code></cite>
  </blockquote>
  <p><code>(2,4,6)</code> is also a natural structural pick independent of any
  board: qubits 2 and 4, and 2 and 6, are hardware-connected, so the triple is a
  connected star centred on a degree-3 qubit. The strong game vocabulary in this
  project belongs to rungs 1 and 2, where the domain was reconstructible and
  GPT said so out loud; it does not carry into rung 3, and the earlier version
  of this page was wrong to import it.</p>
  <p>Haiku is the arm that behaves like a remembered board. It put 72 of 180
  placements on row-major lines and 56 on the single triple
  <code>(0,4,8)</code>, held from generation 2 to generation 52, and collected
  exactly one true line in the process. Recall is visible in this data. It is
  visible in the arm with the <em>lowest</em> score, not the highest.</p>

  <h3>The accuracy trend is the tell</h3>
  <p>If the motif were being found, and if finding it were doing any work, motif
  usage and accuracy would move together. Usage spans a hundredfold across the
  three arms. Best test accuracy is 64.2%, 65.0% and 62.3%: flat within three
  points, and ordered the <em>wrong way</em>, with the highest-usage arm last.
  Best fitness tells the same story at 0.615, 0.628 and 0.625, a spread of
  0.013.</p>
  <p>The single most damaging fact is downstream of that. None of the three best
  circuits uses a winning line. GPT's best program, at generation 49, contains no
  three-qubit gates at all. Its eighteen placements were tried and discarded by
  the score, which is what should happen to a hypothesis that is not paying for
  itself.</p>

  <h3>Tighten the measure and the claim disappears</h3>
  <p>Every step from the loosest measure to the strictest costs the claim
  something, monotonically, and the strictest measure is the one that cannot be
  reached by recall or by a preference for well-connected qubits.</p>
</div>

<figure class="wide">
  <div class="plate"><img src="{fig_deflate}" alt="Denominator collapse, motif usage against accuracy, and the claim shrinking as the measure tightens."></div>
  <figcaption class="wrap" style="margin:10px auto 0;">(a) The denominator is a
  choice: GPT placed 18 three-qubit gates where Haiku placed 180. (b) Usage
  spans a hundredfold while test accuracy stays flat and runs the wrong way.
  (c) GPT-5.6-sol's claim across four measures of increasing strictness:
  67% of placements, 43% of distinct triples, 38% of the eight lines, and 0 of
  the two hidden lines.</figcaption>
</figure>

<div class="wrap">
  <h3>What survives</h3>
  <p>There is a weak, consistent ordering in <em>coverage</em>: Haiku touched 1
  of the 8 lines, Sonnet 2, GPT 3. That ordering is real but small, is not
  significant against the connectivity-matched baseline, is not accompanied by
  any accuracy gain, and stops dead at the hidden lines, where all three arms
  score zero. It is compatible with a mild capability effect and equally
  compatible with GPT simply being the arm that recalls the game hardest.</p>
</div>

<h2 class="wrap" id="ranking">Is it a capability ranking?</h2>
<div class="wrap">
  <p>The tempting reading of <code>1/180 &middot; 3/52 &middot; 12/18</code> is that
  the arms are ordered by model strength, so a better model is better at
  zero-context tic-tac-toe. The ordering is real in that one statistic. It
  appears in no other. Every measure whose denominator is fixed by the
  experiment rather than chosen by the model either reverses it or shows
  nothing.</p>

  <h3>The outcome measures</h3>
  <p>Fitness is what the search optimises and the only quantity the model ever
  sees; accuracy is reported for the circuit that fitness selected, the same
  convention as the rung-3 table above. Across the three zero-context tasks
  GPT-5.6-sol is first on neither measure, on any task.</p>
</div>

<div class="wide tablewrap">
  <table>
    <thead>
      <tr><th>Task</th><th></th><th>Haiku 4.5</th><th>Sonnet 5</th><th>GPT-5.6-sol</th><th>Best</th></tr>
    </thead>
    <tbody>
      <tr><td rowspan="2"><code>zc-ttt</code><br><span style="font-weight:400">winning lines</span></td>
        <td>best fitness</td><td class="mono">0.6147</td><td class="mono win">0.6277</td><td class="mono">0.6246</td><td>Sonnet</td></tr>
      <tr><td>test acc of that circuit</td><td class="mono">64.2%</td><td class="mono win">65.0%</td><td class="mono off">62.3%</td><td>Sonnet, GPT last</td></tr>
      <tr><td rowspan="2"><code>zc-sn</code><br><span style="font-weight:400">S<sub>8</sub> invariant</span></td>
        <td>best fitness</td><td class="mono win">0.9148</td><td class="mono">0.8924</td><td class="mono">0.9034</td><td>Haiku</td></tr>
      <tr><td>test acc of that circuit</td><td class="mono">89.3%</td><td class="mono win">90.3%</td><td class="mono">90.0%</td><td>Sonnet</td></tr>
      <tr><td rowspan="2"><code>zc-su2</code><br><span style="font-weight:400">spin singlets</span></td>
        <td>best fitness</td><td class="mono">0.7158</td><td class="mono">0.8027</td><td class="mono">0.8027</td><td rowspan="2">saturated,<br>uninformative</td></tr>
      <tr><td>best test acc</td><td class="mono">100%</td><td class="mono">100%</td><td class="mono">100%</td></tr>
    </tbody>
  </table>
</div>

<div class="wrap">
  <p>The <code>zc-su2</code> arm decides nothing: every arm reaches 100% accuracy
  within nine generations and the two leaders tie at an identical 0.8027, which
  is the flat-fitness artefact that prompted the v2 redesign. That leaves two
  informative tasks, won by two different models, neither of them the one the
  67% points at.</p>

  <h3>Comparing whole populations rather than the single best</h3>
  <p>Best-of-80 is one order statistic from one seed, so it is noisy by
  construction. Comparing the full distribution of scored proposals on
  <code>zc-ttt</code> is the sharper test, and it splits the arms two-to-one
  rather than three ways:</p>
</div>

<div class="wide tablewrap">
  <table>
    <thead>
      <tr><th></th><th>n scored</th><th>median fitness</th><th>mean fitness</th></tr>
    </thead>
    <tbody>
      <tr><td>Haiku 4.5</td><td>59</td><td class="mono">0.5608</td><td class="mono">0.5589</td></tr>
      <tr class="key"><td>Sonnet 5</td><td>76</td><td class="mono">0.5812</td><td class="mono">0.5822</td></tr>
      <tr><td>GPT-5.6-sol</td><td>73</td><td class="mono">0.5549</td><td class="mono">0.5578</td></tr>
    </tbody>
  </table>
</div>

<div class="wrap">
  <p>Sonnet sits above both others (Mann&ndash;Whitney, Sonnet vs GPT
  <span class="mono">p = 7&times;10<sup>-9</sup></span>; Sonnet vs Haiku
  <span class="mono">p = 2&times;10<sup>-8</sup></span>), and GPT and Haiku are
  statistically indistinguishable from each other
  (<span class="mono">p = 0.64</span>). The ordering that survives is
  Sonnet &gt; {GPT &asymp; Haiku}: not the claimed ranking, and it does not hold
  on <code>zc-sn</code>.</p>

  <h3>The one difference that is robust</h3>
  <p>Haiku writes more programs that fail to compile or train. That gap is large
  and significant, and it is the only model difference in the zero-context runs
  that reproduces cleanly:</p>
</div>

<div class="wide tablewrap">
  <table>
    <thead>
      <tr><th></th><th>Programs scored / written</th><th>Rate</th><th>vs Haiku</th></tr>
    </thead>
    <tbody>
      <tr><td>Haiku 4.5</td><td class="mono">59 / 80</td><td class="mono off">73.8%</td><td>&mdash;</td></tr>
      <tr><td>Sonnet 5</td><td class="mono">76 / 79</td><td class="mono win">96.2%</td><td class="mono">p = 9&times;10<sup>-5</sup></td></tr>
      <tr><td>GPT-5.6-sol</td><td class="mono">73 / 80</td><td class="mono win">91.2%</td><td class="mono">p = 0.006</td></tr>
    </tbody>
  </table>
</div>

<div class="wrap">
  <p>Sonnet and GPT are not separable here either
  (<span class="mono">p = 0.33</span>, Fisher exact). So the shape is
  {Sonnet, GPT} &gt; Haiku, and what it measures is whether a model can emit a
  circuit specification that satisfies the gate schema. That is instruction
  following, not discovery, and it says nothing about tic-tac-toe.</p>
</div>

<div class="verdict fail">
  <span class="lab">On the capability reading</span>
  <p>Three models, one seed each, is three data points. The claimed ordering is
  perfectly rank-correlated with how rarely each arm used three-qubit gates
  (56, 21 and 14 programs), and with n = 3 those two explanations cannot be
  separated. Nothing here licenses a statement about model strength on this
  task, in either direction: the honest reading is that all three arms failed
  the same test, and the differences between them are noise, task-dependent, or
  about syntax.</p>
</div>

<div class="verdict fail">
  <span class="lab">Five lessons that generalise</span>
  <p><strong>A percentage whose denominator the agent chooses is not comparable
  across agents.</strong> Report the counts. <code>12/18</code> and
  <code>1/180</code> are honest in a way that 67% and 0.6% are not.</p>
  <p><strong>An evolutionary population is not a sample.</strong> Inheritance
  makes gates pseudo-replicate, so the unit of analysis has to be the distinct
  decision, not the gate. Switching the unit alone moves p from
  6&times;10<sup>-9</sup> to 0.02; switching the baseline alone moves it to
  5.6&times;10<sup>-4</sup>; doing both gives 0.29. The two corrections are
  independent, and each is needed.</p>
  <p><strong>Recall can score hits on the true target</strong> whenever the
  remembered set and the true set overlap at all. Designing the target so the two
  are disjoint is what makes the test sharp, and it is exactly what the hidden
  lines do.</p>
  <p><strong>Check the structure against the metric it is supposed to
  improve.</strong> A claim that the search found useful structure, unaccompanied
  by any movement in the quantity that structure should improve, is not a finding
  about the search. It is a finding about the statistic.</p>
  <p><strong>Three models is three data points.</strong> An ordering across
  three arms is rank-correlated with every other three-way ordering in the run,
  including uninteresting ones like how often each arm reached for the gate
  being counted. Before reading a model ranking off a metric, check that the
  ranking holds on the quantity being optimised, and on a second task.
  Here it does neither.</p>
</div>

<h2 class="wrap" id="trajectories">How each model reached its best circuit</h2>
<div class="wrap">
  <p>Every accepted proposal carries the model's own written rationale for the
  edit. Reading the chain of proposals that each set a new best score gives the
  design history of the winning circuit: what was tried, what was kept, and what
  was measured and thrown away. The three arms tell noticeably different
  stories, and none of them is a story about winning lines.</p>
  <p>All three independently reached for three-qubit gates within the first few
  generations. Two of them measured the result and removed them again. The
  third kept them and finished last.</p>
  <div class="note" style="margin:14px 0;">
    <strong>What this reconstruction can and cannot say.</strong> ShinkaEvolve
    records <code>parent_id</code>, <code>code_diff</code> and the archive and
    top-<em>k</em> inspiration ids it showed the proposer, which is what would
    settle exactly which earlier circuits each edit merged. The zero-context
    databases are still on the cluster and the export used for this page kept
    only id, code, generation, score and metrics. So the lineage below is the
    record-setting chain reconstructed from generation order, the realised
    circuit specs, and each proposal's stated reasoning. Where a rationale
    refers to an earlier program it is quoted rather than inferred.
  </div>
</div>

<h3 class="wrap">GPT-5.6-sol &mdash; prune, tie, probe, discard</h3>
<div class="wide tablewrap">
  <table>
    <thead><tr><th>Gen</th><th>Score</th><th>Params</th><th>Edit</th><th>3-qubit gates</th></tr></thead>
    <tbody>
      <tr><td>0</td><td class="mono">0.5220</td><td>162</td><td>seed: RY, RZ&times;2, 12 fixed CZ</td><td>&mdash;</td></tr>
      <tr><td>2</td><td class="mono">0.5744</td><td>108</td><td><code>remove_commuting_rz_redundancy</code></td><td>&mdash;</td></tr>
      <tr><td>16</td><td class="mono">0.5787</td><td>90</td><td><code>symmetry_tied_phase</code>, RZ tied on (1,4) (2,3) (5,6)</td><td>&mdash;</td></tr>
      <tr><td>19</td><td class="mono">0.5837</td><td>96</td><td><code>add_zzz_correlation_probe</code></td><td class="win">ZZZ on (2,4,6)</td></tr>
      <tr><td>34</td><td class="mono">0.5857</td><td>96</td><td><code>symmetry_hub_cry</code>, probe removed</td><td class="off">dropped</td></tr>
      <tr><td>41</td><td class="mono">0.6009</td><td>96</td><td><code>layered_crz_hub</code>, single CRZ at (0,7)</td><td>&mdash;</td></tr>
      <tr class="key"><td>49</td><td class="mono">0.6246</td><td>180</td><td><code>graph_tied_dual_rotation</code>, two RY/RZ layers</td><td>none</td></tr>
    </tbody>
  </table>
</div>
<div class="wrap">
  <p>The largest single gain in the whole run, +0.052 at generation 2, comes
  from a purely algebraic observation with no reference to the data:</p>
  <blockquote>
    Every CZ gate is diagonal in the computational basis and therefore commutes
    with RZ rotations. Consequently each post RZ can be moved across the CZ
    network and merged with the corresponding pre RZ, making nine parameters per
    block functionally redundant.
    <cite>GPT-5.6-sol, generation 2</cite>
  </blockquote>
  <p>From there it compresses: 162 parameters to 108, then to 90 by tying phases
  across pairs it calls graph-symmetric. The three-qubit gate arrives at
  generation 19 as a single explicitly labelled probe, earns +0.005, and is
  deleted fifteen generations later in favour of one two-qubit rotation on the
  highest-degree edge:</p>
  <blockquote>
    The costly three-qubit interaction and peripheral controlled rotations are
    omitted; instead, the high-connectivity edge (0,7) uses CRY to learn
    correlation strength directly.
    <cite>GPT-5.6-sol, generation 34</cite>
  </blockquote>
  <p>The winning circuit at generation 49 abandons the compression strategy
  entirely, going back up to 180 parameters by stacking a second full RY/RZ
  layer after the entangler. It contains no three-qubit gates at all. Every
  triple GPT ever placed, including the one on a true line, had been tried and
  rejected by the score before the run finished.</p>
</div>

<h3 class="wrap">Sonnet 5 &mdash; trainable entanglement, then regularise it</h3>
<div class="wide tablewrap">
  <table>
    <thead><tr><th>Gen</th><th>Score</th><th>Params</th><th>Edit</th><th>3-qubit gates</th></tr></thead>
    <tbody>
      <tr><td>0</td><td class="mono">0.5220</td><td>162</td><td>seed</td><td>&mdash;</td></tr>
      <tr><td>1</td><td class="mono">0.5788</td><td>234</td><td><code>parametrized_entangling_layer</code>, all 12 CZ &rarr; CRZ</td><td>&mdash;</td></tr>
      <tr><td>6</td><td class="mono">0.5950</td><td>144</td><td><code>add_trainable_entanglement_reduce_redundancy</code></td><td>&mdash;</td></tr>
      <tr><td>8</td><td class="mono">0.6032</td><td>180</td><td>CRZ + CRY on two axes, ZZZ removed</td><td class="off">dropped</td></tr>
      <tr class="key"><td>17</td><td class="mono">0.6277</td><td>162</td><td><code>param_sharing_hub_reduction</code></td><td>none</td></tr>
    </tbody>
  </table>
</div>
<div class="wrap">
  <p>Sonnet finds the biggest structural idea immediately, at generation 1: make
  the entanglement trainable. It is also the only arm that states an explicit
  verdict on three-qubit gates, having tried them at generation 3 and read the
  number that came back:</p>
  <blockquote>
    &hellip; the version that added RZ_pre plus ZZZ three-qubit terms (0.55,
    likely too deep and overparametrised without added benefit) &hellip; this
    edit removes the ZZZ three-qubit interactions, which hurt performance and
    added depth.
    <cite>Sonnet 5, generation 8</cite>
  </blockquote>
  <p>The final edit is the cleanest piece of reasoning in the three runs. It
  diagnoses its own overfitting from the train-validation split and fixes it by
  tying parameters rather than deleting gates, keeping the expressivity and
  dropping 18 parameters: three CRZ gates that had been made independent are
  made to share a parameter with an existing CRZ on the same hub qubit. That
  single move is worth +0.024 and produces the best circuit in the entire
  zero-context tic-tac-toe experiment.</p>
</div>

<h3 class="wrap">Haiku 4.5 &mdash; adds three-qubit gates early and never lets go</h3>
<div class="wide tablewrap">
  <table>
    <thead><tr><th>Gen</th><th>Score</th><th>Params</th><th>Edit</th><th>3-qubit triples carried</th></tr></thead>
    <tbody>
      <tr><td>0</td><td class="mono">0.5220</td><td>162</td><td>seed</td><td>&mdash;</td></tr>
      <tr><td>2</td><td class="mono">0.5593</td><td>120</td><td><code>reduce_params_add_parametrized_entanglement</code></td><td class="mono">(0,4,8) (1,5,6)</td></tr>
      <tr><td>9</td><td class="mono">0.5608</td><td>90</td><td>rotation layers widened</td><td class="mono">(0,4,8) (1,5,6)</td></tr>
      <tr><td>10</td><td class="mono">0.5635</td><td>126</td><td><code>split_rz_layers_add_crz</code></td><td class="mono">(0,4,8) (1,5,6)</td></tr>
      <tr><td>14</td><td class="mono">0.5666</td><td>162</td><td><code>parameterized_entanglement_upgrade</code>, adds CCRZ</td><td class="mono">4 triples</td></tr>
      <tr><td>18</td><td class="mono">0.5911</td><td>114</td><td><code>share_crz_params_add_zzz</code></td><td class="mono">(0,4,8) (1,5,6) (2,6,7)</td></tr>
      <tr><td>26</td><td class="mono">0.5977</td><td>114</td><td><code>shift_zzz_triplet_for_better_correlations</code></td><td class="mono">(0,4,8) (2,5,8) (2,6,7)</td></tr>
      <tr><td>30</td><td class="mono">0.5997</td><td>174</td><td><code>balanced_entanglement_ansatz</code></td><td class="mono">(0,4,8) (2,5,7) (1,3,6)</td></tr>
      <tr class="key"><td>52</td><td class="mono">0.6147</td><td>174</td><td><code>restore_individual_ry_reduce_rz_add_cnot</code></td><td class="mono">(0,4,8) (2,5,7) (1,3,6)</td></tr>
    </tbody>
  </table>
</div>
<div class="wrap">
  <p>Haiku puts three-qubit gates in at generation 2 and every subsequent record
  carries them. <code>(0,4,8)</code> in particular survives from generation 2 to
  generation 52 untouched, which is the whole of its 56-placement count: one
  decision, inherited fifty-six times. This is the pseudoreplication described
  above, visible as a design history rather than as a statistic.</p>
  <p>When it does move a triple, the stated reason is geometric and has nothing
  to do with lines:</p>
  <blockquote>
    Replace the second ZZZ block from [1,5,6] to [2,5,8] &hellip; The new
    configuration [0,4,8] and [2,5,8] provides better spatial distribution
    across the qubit lattice.
    <cite>Haiku 4.5, generation 26</cite>
  </blockquote>
  <p>It is searching over how to spread three-qubit couplings across the
  register, not over which triples are predictive. None of the triples in its
  final circuit is a true line, and the arm that used the motif vocabulary most
  heavily finished with the lowest score of the three.</p>
</div>

<div class="verdict fail">
  <span class="lab">What the design histories show</span>
  <p>The three winning circuits are reached by three different routes:
  algebraic pruning then re-expansion (GPT), trainable entanglement then
  parameter tying (Sonnet), and incremental higher-order coupling (Haiku). Two
  of the three tested three-qubit interactions, measured them, and wrote down
  why they were removing them. Not one proposal in 239 across the three arms
  mentions the game, a board, or a winning line. Whatever these searches were
  doing, they were doing circuit engineering against a scalar, and the motif
  never entered the reasoning.</p>
</div>

<h2 class="wrap">How the models reasoned</h2>
<div class="wrap">
  <p>Every proposal carries a written rationale. <strong>The vocabulary counts
  in this section are rungs 1 and 2 only.</strong> Game vocabulary appears in
  92% of the run that was handed the answer, and still in 10&ndash;30% once the
  game is never named, so concealment at rung 2 worked only partly. At rung 3 it
  worked completely: the strict rate there is zero in all three arms, and the
  <a href="#trajectories">design histories</a> above contain no game reasoning
  of any kind.</p>
</div>

<figure class="wide">
  <div class="plate"><img src="{fig_vocab}" alt="Share of proposals using game vocabulary, by run and over generations."></div>
  <figcaption class="wrap" style="margin:10px auto 0;">The leaked run engages the
  game from its first edit and never stops.</figcaption>
</figure>

<div class="wrap">
  <p>GPT-5.6-sol reconstructed the task from the data alone and said so:</p>
  <blockquote>
    an IQP-style feature extractor aligned to the eight winning lines of a 3x3
    board &hellip; parameters shared across rows, columns, and diagonals
    <cite>GPT-5.6-sol, generation 9</cite>
  </blockquote>
  <p>That gives a clean test. A model that <em>recalled</em> the game knows the
  lines in the standard layout, which the permutation moved. A model that
  <em>discovered</em> them would hit the true ones.</p>
</div>

<figure class="wide">
  <div class="plate"><img src="{fig_recall}" alt="Gates on remembered versus true lines, and the score rejecting the recalled motif."></div>
  <figcaption class="wrap" style="margin:10px auto 0;">Across five generations it
  placed 8 of 8 gates on the lines of an <em>unpermuted</em> board and 1 of 8 on
  the true ones. Those attempts score below what it had already reached.</figcaption>
</figure>

<div class="verdict fail">
  <span class="lab">Verdict</span>
  <p>The search never discovered the motif. Usage tracks how much was supplied,
  the three models disagree, most of the surviving signal is a connectivity
  preference unrelated to the task, and no variant at any horizon found either
  line that can only be reached from the score. The model that did reconstruct
  the domain proposed the lines it remembered, measured them, and abandoned
  them.</p>
  <p>The motif itself is good structure: independent work on this exact task
  finds motif-aligned gates worth about +0.11 test accuracy. What this removes is
  the inference from <em>this circuit uses the motif</em> to <em>this search
  found the motif</em>.</p>
</div>

<h2 class="wrap">What the model was told</h2>
<div class="wrap">
  <details class="prompt leak">
    <summary>Rung 1: the starter file<span class="tag">the answer, outright</span></summary>
    <p style="font-size:15px;color:var(--muted);margin:10px 0 0;">This sits above
    the editable region, so it entered the model's context in full every
    generation.</p>
    <pre>{LEAKY}</pre>
  </details>
  <details class="prompt">
    <summary>Rung 2: the anonymised task message<span class="tag">no game named</span></summary>
    <p style="font-size:15px;color:var(--muted);margin:10px 0 0;">Search it for
    "tic-tac-toe", "board", "row", "column", "diagonal", "corner" or "winning".
    None appear. It does give the wiring, because that limits which circuits are
    legal.</p>
    <pre>{MOTIF}</pre>
  </details>
</div>
"""

# ---------------------------------------------------------------- task: graph
GRAPH = """
<header class="page wrap">
  <h1>Graph connectedness</h1>
  <p class="dek">Two variants that differ by one sentence. The sentence turns out
  to be the entire result.</p>
  <p class="byline">Task 2 &nbsp;·&nbsp; the answer is a symmetry, which can be worked out</p>
</header>

<div class="wrap">
  <p>Each record says which of the 28 possible connections among eight nodes are
  present, and the label depends only on the shape of the network, not on which
  node is called which. Renaming the nodes is therefore an exact symmetry. A
  circuit that respects it treats all eight wires alike.</p>

  <p>This is the fair test the tic-tac-toe task cannot be. Winning lines are a
  <em>convention</em>: you either know the game or you do not. A symmetry can in
  principle be read off the shape of the data. Neither variant's instructions or
  starter file mentions symmetry, invariance, permutation or any group; we
  grepped for all of them. Both allow gates on any pair, so the connectivity
  confound does not arise.</p>
</div>

<h2 class="wrap">The task, concretely</h2>
<div class="wrap">
  <p>The classifier decides a yes/no property of a small network: whether eight
  nodes, wired together in some pattern, form one connected piece. A record is
  the complete wiring list, one binary feature for each of the 28 possible links
  between eight nodes (28 is the number of unordered pairs of eight things), and
  the label is +1 or &minus;1 for connected or not. Renaming the nodes changes
  none of that, so the task carries an exact symmetry: the full permutation
  group on eight labels, order 40,320. We verified the symmetry holds in the
  data, not just in principle: the 1,350 records fall into 815
  relabelling-invariant classes, and every class carries a single label.</p>
</div>

<h2 class="wrap">What the model sees, and what it writes</h2>
<div class="wrap">
  <p>The evolving model never sees a record. Fixed code trains and scores each
  candidate, and the model gets numbers back. The data enters the
  <em>circuit</em> through a fixed feature map: feature <i>k</i> becomes a
  two-qubit ZZ phase coupling on qubit pair <i>k</i>, re-applied between ansatz
  blocks so the circuit reads the input more than once. The readout is also
  fixed: a Z measurement averaged over all eight wires, through a trainable gain
  and bias, regressed to the &plusmn;1 label. Between encoder and readout sits
  the one thing the model writes, the <code>ANSATZ_SPEC</code> gate list:</p>
</div>

<div class="wide tablewrap">
  <table>
    <thead>
      <tr><th>Gates</th><th>Acts on</th><th>Parametrized</th><th>Where it may go</th></tr>
    </thead>
    <tbody>
      <tr><td><code>RX</code>, <code>RY</code>, <code>RZ</code></td><td>1 qubit</td><td>yes</td><td>any of the eight qubits</td></tr>
      <tr><td><code>CNOT</code>, <code>CZ</code></td><td>2 qubits</td><td>no</td><td>any pair</td></tr>
      <tr><td><code>CRX</code>, <code>CRY</code>, <code>CRZ</code></td><td>2 qubits</td><td>yes</td><td>any pair</td></tr>
    </tbody>
  </table>
</div>

<div class="wrap">
  <p>Reusing a parameter name shares that parameter; invalid gate lists are
  rejected. Unlike tic-tac-toe there is no hardware restriction: all 28 pairs
  are legal, so the 28 pairs the encoder writes onto are exactly the 28 pairs
  the ansatz may couple, and a preference for well-connected qubits cannot
  masquerade as structure.</p>
</div>

<h2 class="wrap">What the ideal answer looks like</h2>
<div class="wrap">
  <p>The label ignores node names, so the ideal circuit ignores wire names. An
  exactly equivariant ansatz treats the eight wires as interchangeable: every
  wire gets the same gates under the same shared parameter names, and every
  pair the same coupling, one parameter per layer rather than one per wire.
  Relabelling the wires then maps the circuit onto itself, and the prediction
  can depend only on the shape of the input graph, which is precisely what the
  label depends on. The best circuit found under rung 1 is exactly this:
  rotation angles shared across all eight qubits and CZ entanglers covering the
  complete graph, 26 parameters in place of the seed's 146, and the best test
  accuracy of any arm at 96.0%.</p>
  <p>Equivariance is measured, not asserted. A symmetry score of 1.0 means
  exact: the gate list is a union of whole orbits with tied names, and feeding
  the circuit a record and a randomly relabelled copy of the same record
  changes the prediction by exactly nothing. Partial sharing, such as tying
  even wires to one angle and odd wires to another, scores in between, which is
  how the zero-context arms' best circuits land at 0.46, 0.38 and 0.09 without
  any of them being equivariant in the sense that matters.</p>
</div>

<h2 class="wrap">The two variants</h2>
<div class="wide ladder two">
  <div class="rung given">
    <span class="step">Rung 1</span>
    <h4>Premise stated</h4>
    <p class="meta">51&ndash;78 generations · three models separately</p>
    <ul class="chips">
      <li class="yes">Task message: feature k couples a fixed <em>qubit pair</em></li>
      <li class="yes">Starter file repeats it as <code>FEATURE_PAIRS[k]</code></li>
      <li class="yes">The number 28 is stated</li>
      <li class="no">No symmetry, permutation or group named anywhere</li>
    </ul>
    <div class="outcome">
      <span class="lab">Exactly equivariant circuits</span>
      <span class="big off">5</span>
      <span class="sub">GPT-5.6-sol, first at generation 33. 96.0% test, 26 parameters.</span>
    </div>
  </div>

  <div class="rung none">
    <span class="step">Rung 2</span>
    <h4>Premise removed</h4>
    <p class="meta">80 generations · the same three models</p>
    <ul class="chips">
      <li class="no">Nothing about what the features are</li>
      <li class="no">The number 28 never appears</li>
      <li class="no">Whole pipeline moved into an unshown module</li>
      <li class="yes">Same data, same reward, same gates, longer budget</li>
    </ul>
    <div class="outcome">
      <span class="lab">Exactly equivariant circuits</span>
      <span class="big win">0</span>
      <span class="sub">No model, no generation. Test accuracy stalls six points lower.</span>
    </div>
  </div>
</div>

<h2 class="wrap">The sentence that made the difference</h2>
<div class="wrap">
  <p>The two variants differ in the starter file's docstring, which ShinkaEvolve
  shows the model in full at every generation.</p>
</div>

<div class="wide diff">
  <div class="hd">Rung 1 &nbsp;·&nbsp; what was removed</div>
  <pre class="minus">{HINT_SEED}</pre>
  <div class="hd">Rung 2 &nbsp;·&nbsp; what replaced it</div>
  <pre class="plus">{ZC_SEED}</pre>
</div>

<div class="wrap">
  <p>From <em>features are qubit pairs</em> and <em>there are 28 of them</em>,
  the rest is arithmetic: 28 is the number of pairs of 8 things, so the records
  are graphs; a graph's label cannot depend on names; therefore treat all eight
  wires identically. That is one deductive step, and it is the step the model
  took.</p>
</div>

<h2 class="wrap">What the model said when it worked</h2>
<div class="wrap">
  <p>At generation 33, GPT-5.6-sol proposed a circuit it named
  <code>permutation_equivariant_ansatz</code>:</p>
  <blockquote>
    Exploit the likely graph structure of the 28 binary features, which
    correspond exactly to all unordered pairs of eight qubits &hellip; rotation
    parameters are shared across all qubits, and CZ gates cover the complete
    graph. This aligns the circuit with relabeling-invariant graph
    classification.
    <cite>GPT-5.6-sol, generation 33, premise stated</cite>
  </blockquote>
  <p>The score jumped from 0.869 to 0.937 in that generation and the arm never
  went back. Note where the derivation starts: with the premise the starter file
  supplied.</p>
</div>

<figure class="wide">
  <div class="plate"><img src="{fig_symmetry}" alt="Symmetry of proposals over generations, the score before and after, and accuracy against parameters."></div>
  <figcaption class="wrap" style="margin:10px auto 0;">Rung 1. Symmetry jumps to
  exact at generation 33 and stays (a). The score jumps with it (b). More
  symmetric circuits use fewer parameters and score higher (c).</figcaption>
</figure>

<h2 class="wrap">What happened without it</h2>
<figure class="wide">
  <div class="plate"><img src="{fig_zerocontext}" alt="The graph task with and without the sentence naming the feature-qubit correspondence."></div>
  <figcaption class="wrap" style="margin:10px auto 0;">(a) Told the features are
  qubit pairs: exact equivariance from generation 33. (b) Not told, at a longer
  horizon: three arms plateau between 0.1 and 0.5 and none reaches it. (c) The
  sentence is worth six points of test accuracy.</figcaption>
</figure>

<div class="wide tablewrap">
  <table>
    <thead>
      <tr><th></th><th class="grp" colspan="3">Premise stated</th>
      <th class="grp vrule" colspan="3">Premise removed</th></tr>
      <tr><th></th><th>GPT-5.6</th><th>Haiku</th><th>Sonnet</th>
      <th class="vrule">GPT-5.6</th><th>Haiku</th><th>Sonnet</th></tr>
    </thead>
    <tbody>
      <tr><td>Generations</td><td>64</td><td>78</td><td>51</td><td class="vrule">80</td><td>80</td><td>80</td></tr>
      <tr class="key"><td>Exactly equivariant circuits</td><td class="win">5</td><td>0</td><td>0</td><td class="off vrule">0</td><td class="off">0</td><td class="off">0</td></tr>
      <tr><td>First at generation</td><td>33</td><td>never</td><td>never</td><td class="vrule">never</td><td>never</td><td>never</td></tr>
      <tr><td>Symmetry of best circuit</td><td>0.96</td><td>0.66</td><td>0.18</td><td class="vrule">0.46</td><td>0.38</td><td>0.09</td></tr>
      <tr><td>Mean symmetry</td><td>0.53</td><td>0.53</td><td>0.15</td><td class="vrule">0.32</td><td>0.36</td><td>0.14</td></tr>
      <tr><td>Test accuracy</td><td class="win">96.0%</td><td>92.0%</td><td>92.0%</td><td class="vrule">90.0%</td><td>89.3%</td><td>89.0%</td></tr>
      <tr><td>Parameters</td><td>26</td><td>38</td><td>98</td><td class="vrule">62</td><td>50</td><td>122</td></tr>
    </tbody>
  </table>
</div>

<div class="wrap">
  <p class="note">The starting circuit scores 86.7% with 146 parameters at
  symmetry 0.15. Exactness, not the average, is what separates the conditions:
  the Haiku arm with the premise averaged the same symmetry as the GPT arm and
  still never reached 1.0, so a high average measures parameter sharing rather
  than the symmetry.</p>
</div>

<h2 class="wrap">They did propose symmetry, just the wrong one</h2>
<div class="wrap">
  <p>Ten or eleven proposals per arm use symmetry vocabulary without the premise,
  so the idea was not absent. What they mean by it is local: sharing angles
  between even and odd wires, mirroring a layer, tying a chain back on itself.
  The best zero-context proposal explains that it will "share the initial RY
  angles by wire parity, replacing eight independent parameters with two".</p>

  <p>Parity sharing is a subgroup of order two. The task's symmetry has order
  40,320. One proposal in 232 uses the word "relabel" at all. The search was
  doing parameter economy, which the score also rewards, and never arrived at the
  hypothesis the score would have paid much more for.</p>
</div>

<div class="verdict fail">
  <span class="lab">Verdict</span>
  <p>The symmetry was derivable in both variants: the data never changed and the
  score paid for it either way. What changed was one sentence of description.
  This is the result that most sharpened the conclusion, because it rules out the
  comfortable reading of the tic-tac-toe failure. It is not that the search finds
  derivable structure and fails on conventions. It is that the search carries a
  <em>stated</em> premise one step, and does not recover the premise itself.</p>
  <p>This variant also caught us. We built rung 1, read the derivation as
  discovery, and wrote it up that way. The leak was in the same channel as the
  tic-tac-toe leak, and got past us because a sentence about the encoding does
  not look like an answer.</p>
</div>

<h2 class="wrap">What the model was told</h2>
<div class="wrap">
  <details class="prompt leak">
    <summary>Rung 1: task message<span class="tag">states the premise</span></summary>
    <p style="font-size:15px;color:var(--muted);margin:10px 0 0;">Never mentions
    symmetry, permutation, invariance or graphs. The fourth architecture line
    states that each feature is a coupling on a qubit pair.</p>
    <pre>{SN}</pre>
  </details>
  <details class="prompt">
    <summary>Rung 2: task message<span class="tag">premise removed</span></summary>
    <p style="font-size:15px;color:var(--muted);margin:10px 0 0;">The number 28
    does not appear, and nothing describes the data.</p>
    <pre>{ZC}</pre>
  </details>
</div>
"""

# ----------------------------------------------------------------- task: spin
SPIN = """
<header class="page wrap">
  <h1>Spin states</h1>
  <p class="dek">A task that measures nothing, in two different ways. Reported
  because the failure is instructive.</p>
  <p class="byline">Task 3 &nbsp;·&nbsp; the negative control that turned into a lesson</p>
</header>

<div class="wrap">
  <p>Inputs are quantum states of an eight-site spin ring, all rotationally
  balanced, and the label is which phase the ring is in. The structure that
  matters is the rotationally invariant coupling: tying the XX, YY and ZZ
  interactions on a pair to a single shared parameter. The gate vocabulary offers
  the three separately, so tying them is a deliberate, score-driven choice, and
  it makes a clean binary threshold in the same way exact equivariance does for
  the graph task.</p>
</div>

<h2 class="wrap">The physics</h2>
<div class="wrap">
  <p>The states are ground states of eight spin-&frac12; particles on a ring
  with Heisenberg coupling,
  H = &Sigma;<sub>i</sub> J<sub>i</sub>
  (X<sub>i</sub>X<sub>i+1</sub> + Y<sub>i</sub>Y<sub>i+1</sub> +
  Z<sub>i</sub>Z<sub>i+1</sub>), where the bond strengths J<sub>i</sub>
  alternate around the ring: strong, weak, strong, weak. When the even bonds
  are the strong ones, neighbouring spins pair up across the even bonds; when
  the odd bonds are, across the odd. These are the two dimerized phases, and
  the label says which one a state is in. The dataset samples coupling ratios
  near the transition and adds per-bond disorder, computes each ground state
  by exact diagonalization, and ships it as an opaque state vector.</p>
  <p>Every one of these states has total spin exactly zero, which we verified
  directly. No spin direction is special, so no measurement of any single spin
  distinguishes the phases; only the pattern of correlations between
  neighbouring sites does. That rotational balance is the structure that
  matters here: the Hamiltonian commutes with rotating every spin together, the
  global SU(2) symmetry, and it is a continuous symmetry rather than the finite
  relabelling group of the graph task.</p>
</div>

<h2 class="wrap">What the model sees, and what it writes</h2>
<div class="wrap">
  <p>There is no feature map to design: each input state vector is prepared
  directly on the eight qubits, the candidate block is applied six times, and
  the fixed readout takes the ZZ correlator averaged over the eight ring bonds,
  through a trainable gain and bias, to the &plusmn;1 label. The readout's pair
  list is supplied, but the qubit labels are scrambled by a fixed secret
  permutation, so the ring is not 0, 1, &hellip;, 7 in order, and nothing marks
  which bonds are the strong ones. The model sees the seed file and per-candidate
  numbers, and writes the <code>ANSATZ_SPEC</code> gate list:</p>
</div>

<div class="wide tablewrap">
  <table>
    <thead>
      <tr><th>Gates</th><th>Acts on</th><th>Parametrized</th><th>Where it may go</th></tr>
    </thead>
    <tbody>
      <tr><td><code>RX</code>, <code>RY</code>, <code>RZ</code></td><td>1 qubit</td><td>yes</td><td>any of the eight qubits</td></tr>
      <tr><td><code>CNOT</code>, <code>CZ</code></td><td>2 qubits</td><td>no</td><td>any pair</td></tr>
      <tr><td><code>CRX</code>, <code>CRY</code>, <code>CRZ</code></td><td>2 qubits</td><td>yes</td><td>any pair</td></tr>
      <tr class="key"><td><code>XX</code>, <code>YY</code>, <code>ZZ</code></td><td>2 qubits</td><td>yes</td><td>any pair, offered as three separate gates</td></tr>
    </tbody>
  </table>
</div>

<div class="wrap">
  <p>The last row is the test. The three Ising rotations are in the vocabulary
  but never privileged, and the seed contains no Ising gate at all: it is the
  same generic RY/RZ-plus-CZ block as the other tasks. Any exchange structure
  in a run was evolved there, not inherited.</p>
</div>

<h2 class="wrap">The intended answer</h2>
<div class="wrap">
  <p>The gate-level image of the ring's rotational symmetry is the
  <strong>isotropic exchange</strong>: on a pair of qubits, apply
  <code>XX</code>, <code>YY</code> and <code>ZZ</code> with one shared angle.
  That combination commutes with any global spin rotation; the three gates
  applied with independent angles do not, and neither does any single-qubit
  rotation, which singles out a direction the data does not have. The ideal
  circuit is therefore made only of tied exchanges, placed on the ring's strong
  bonds, and it is drastically economical: a reference circuit of one tied
  exchange layer on the strong sublattice solves the task at ceiling accuracy
  with about four parameters, against the seed's 146.</p>
  <p>The signature is checkable gate by gate, with no judgement calls:
  <code>XX</code> = <code>YY</code> = <code>ZZ</code> under one parameter name,
  and zero single-qubit rotations. No circuit in either variant ever showed it.
  The sections below explain why that outcome, unlike the other two tasks, says
  nothing either way: the task as built could not have selected for the
  structure even in principle.</p>
</div>

<h2 class="wrap">The two variants</h2>
<div class="wide ladder two">
  <div class="rung given">
    <span class="step">Rung 1</span>
    <h4>Original</h4>
    <p class="meta">17&ndash;50 generations · three models separately</p>
    <ul class="chips">
      <li class="yes">Inputs described as precomputed 8-qubit state vectors</li>
      <li class="no">No mention of spin, SU(2), Heisenberg or singlets</li>
      <li class="yes">450 training records</li>
      <li class="yes">Reward: accuracy 0.50, parameter economy 0.05</li>
    </ul>
    <div class="outcome">
      <span class="lab">Circuits tying XX=YY=ZZ</span>
      <span class="big off">0</span>
      <span class="sub">All three arms hit 100% test accuracy by generation 2, 6 and 9.</span>
    </div>
  </div>

  <div class="rung part">
    <span class="step">Rung 2</span>
    <h4>Zero context, reward redesigned</h4>
    <p class="meta">80 generations · the same three models</p>
    <ul class="chips">
      <li class="no">Nothing about the data at all</li>
      <li class="yes">24 training records, so generalisation binds</li>
      <li class="yes">Reward: accuracy 0.30, parameter economy <strong>0.40</strong></li>
      <li class="yes">Economy term rescaled to keep discriminating to ~4 parameters</li>
    </ul>
    <div class="outcome">
      <span class="lab">Circuits tying XX=YY=ZZ</span>
      <span class="big off">0</span>
      <span class="sub">And 49 of Sonnet's 70 proposals contain no gates at all.</span>
    </div>
  </div>
</div>

<h2 class="wrap">Why rung 1 measures nothing</h2>
<div class="wrap">
  <p>Every arm reaches 100% validation and test accuracy within nine generations,
  from a first-proposal score of 0.811. The task saturates before circuit design
  can matter, so nothing distinguishes a good ansatz from a bad one.</p>
</div>

<h2 class="wrap">Why rung 2 measures less than nothing</h2>
<div class="wrap">
  <p>We tried to fix the saturation by making parameter economy the dominant
  term and cutting the training set to 24 records. The search correctly concluded
  that the best circuit is <strong>no circuit</strong>. The best-scoring program
  in the Sonnet arm has zero gates, scores 0.803, and still reaches 100% test
  accuracy.</p>

  <p>That last fact is the real diagnosis. The fixed feature map and readout
  already solve the task, so the searched object is irrelevant, and no reward
  shaping over an irrelevant object can create pressure toward the right answer.
  Strengthening the economy term did not create design pressure, it created an
  incentive to delete the design.</p>
</div>

<figure class="wide">
  <div class="plate"><img src="{fig_spin}" alt="Spin task: accuracy saturated, reward paying for empty circuits, and the coupling never found."></div>
  <figcaption class="wrap" style="margin:10px auto 0;">(a) Test accuracy is
  pinned at 100% in both variants. (b) Under the redesigned reward, score rises
  as gates are removed, and the empty circuit wins. (c) The discovery threshold
  was never crossed by any model in either variant.</figcaption>
</figure>

<div class="wide tablewrap">
  <table>
    <thead>
      <tr><th></th><th class="grp" colspan="3">Original</th>
      <th class="grp vrule" colspan="3">Redesigned reward</th></tr>
      <tr><th></th><th>GPT-5.6</th><th>Haiku</th><th>Sonnet</th>
      <th class="vrule">GPT-5.6</th><th>Haiku</th><th>Sonnet</th></tr>
    </thead>
    <tbody>
      <tr><td>Generations</td><td>50</td><td>17</td><td>35</td><td class="vrule">80</td><td>80</td><td>80</td></tr>
      <tr><td>Best score</td><td>0.998</td><td>0.998</td><td>0.998</td><td class="vrule">0.803</td><td>0.716</td><td>0.803</td></tr>
      <tr><td>Test accuracy</td><td>100%</td><td>100%</td><td>100%</td><td class="vrule">100%</td><td>100%</td><td>100%</td></tr>
      <tr><td>Gates in best circuit</td><td>23</td><td>31</td><td>26</td><td class="vrule">24</td><td>93</td><td class="off">0</td></tr>
      <tr><td>Proposals with no gates</td><td>0</td><td>0</td><td>0</td><td class="vrule">0</td><td>0</td><td class="off">49</td></tr>
      <tr class="key"><td>Circuits tying XX=YY=ZZ</td><td class="off">0</td><td class="off">0</td><td class="off">0</td><td class="off vrule">0</td><td class="off">0</td><td class="off">0</td></tr>
    </tbody>
  </table>
</div>

<div class="verdict fail">
  <span class="lab">Verdict</span>
  <p>This task tests nothing about discovery and should not be read as evidence
  either way. It is reported because the failure mode generalises: a
  structure-discovery benchmark needs the structure to be load-bearing for the
  metric being optimised. If the pipeline around the searched object already
  solves the task, the run measures nothing, and reward shaping cannot rescue
  it.</p>
  <p>To make this task usable, the encoder has to stop solving the problem on its
  own before anything else is tried.</p>
</div>

<h2 class="wrap">What the model was told</h2>
<div class="wrap">
  <details class="prompt">
    <summary>Rung 1: task message<span class="tag">no symmetry named</span></summary>
    <p style="font-size:15px;color:var(--muted);margin:10px 0 0;">Search it for
    "spin", "SU(2)", "rotation", "Heisenberg" or "singlet". None appear. The
    inputs are described only as a precomputed 8-qubit state vector.</p>
    <pre>{SU2}</pre>
  </details>
</div>
"""

FOOTER = """
<div class="wrap">
  <footer>Twelve orchestrator runs on the Yale Bouchet cluster &nbsp;·&nbsp;
  ShinkaEvolve &nbsp;·&nbsp; secret permutation seed 777 &nbsp;·&nbsp;
  proposer models: Claude Haiku 4.5, Claude Sonnet 5, GPT-5.6-sol</footer>
</div>
"""

JS = """
const tabs = document.querySelectorAll('nav.tabs button');
const panes = document.querySelectorAll('section.tab');
function show(id, push) {
  tabs.forEach(b => b.setAttribute('aria-selected', b.dataset.tab === id));
  panes.forEach(p => p.classList.toggle('active', p.id === id));
  if (push !== false) history.replaceState(null, '', '#' + id);
  window.scrollTo({top: 0, behavior: 'instant'});
}
tabs.forEach(b => b.addEventListener('click', () => show(b.dataset.tab)));
document.querySelectorAll('[data-goto]').forEach(
  a => a.addEventListener('click', () => show(a.dataset.goto)));
function route() {
  const id = (location.hash || '#overview').slice(1);
  const el = document.getElementById(id);
  if (!el) { show('overview', false); return; }
  if (el.classList.contains('tab')) { show(id, false); return; }
  // an anchor inside a tab: open its pane first, then bring it into view
  const pane = el.closest('section.tab');
  if (pane) {
    tabs.forEach(b => b.setAttribute('aria-selected', b.dataset.tab === pane.id));
    panes.forEach(p => p.classList.toggle('active', p.id === pane.id));
  }
  el.scrollIntoView({block: 'start'});
}
// Keep the back/forward buttons and pasted #anchor links working: a hash change
// is a same-document navigation, so nothing re-runs unless we listen for it.
window.addEventListener('hashchange', route);
route();
"""

HTML = f"""<title>Discovery or Recall? &mdash; three tasks, several information conditions</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>{CSS}</style>

<div class="topbar">
  <div class="inner">
    <span class="brand">Discovery or Recall?</span>
    <nav class="tabs" role="tablist">
      <button role="tab" data-tab="overview" aria-selected="true">Overview</button>
      <button role="tab" data-tab="ttt"><span class="q">T1</span>Tic-tac-toe</button>
      <button role="tab" data-tab="graph"><span class="q">T2</span>Graph</button>
      <button role="tab" data-tab="spin"><span class="q">T3</span>Spin</button>
    </nav>
  </div>
</div>

<section class="tab active" id="overview">{OVERVIEW}{FOOTER}</section>
<section class="tab" id="ttt">{TTT}{FOOTER}</section>
<section class="tab" id="graph">{GRAPH}{FOOTER}</section>
<section class="tab" id="spin">{SPIN}{FOOTER}</section>

<script>{JS}</script>
"""

out = HTML
for name, uri in FIGS.items():
    out = out.replace("{" + name + "}", uri)
for name, text in PROMPTS.items():
    out = out.replace("{" + name + "}", text)

leftover = re.findall(r"\{([A-Za-z_]+)\}", out)
if leftover:
    print("WARNING unresolved placeholders:", sorted(set(leftover))[:10])

OUT.write_text(out)
print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")
