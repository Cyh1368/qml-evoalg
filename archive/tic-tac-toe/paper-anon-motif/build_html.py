"""Assemble the standalone HTML summary with figures inlined as data URIs."""
import base64
import html
import re
from pathlib import Path

SP = Path(__file__).resolve().parent
OUT = Path.home() / "QuantumAnsatz/qml-ea/tic-tac-toe/paper-anon-motif/summary.html"


def img(name):
    b64 = base64.b64encode((SP / f"{name}.png").read_bytes()).decode()
    return f"data:image/png;base64,{b64}"


FIGS = {n: img(n) for n in
        ["fig_task", "fig_anonymize", "fig_strata", "fig_circuits",
         "fig_trajectory", "fig_summary", "fig_vocab", "fig_recall",
         "fig_symmetry"]}

# The task messages exactly as sent to the model, read from the same dump the
# paper appendix is generated from so the two can never drift apart.
_raw = (SP / "prompts.txt").read_text()
PROMPTS = {}
for _tag in ("MOTIF", "SN", "SU2"):
    _m = re.search(r"<<<<<<<<<<%s\n(.*?)\n>>>>>>>>>>%s" % (_tag, _tag), _raw, re.S)
    PROMPTS[_tag] = html.escape(_m.group(1).strip("\n")) if _m else "(missing)"
PROMPTS["LEAKY"] = html.escape((SP / "leaky_seed.txt").read_text().strip("\n"))

HTML = """<title>Discovery or Recall?</title>
<style>
  :root {
    --paper:#fbfbf9; --ink:#12140f; --muted:#63675f; --rule:#e2e4dd;
    --plate:#ffffff; --band:#f2f3ee;
    --win:#1b7837; --off:#c2453a; --hid:#7b3294;
    --serif: "Iowan Old Style","Palatino Linotype",Palatino,Georgia,"Times New Roman",serif;
    --sans: ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
    --mono: ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --paper:#101210; --ink:#e9eae4; --muted:#9aa096; --rule:#2a2d28;
      --plate:#f7f7f4; --band:#181b18;
      --win:#4faf73; --off:#e0736a; --hid:#b07fd0;
    }
  }
  :root[data-theme="dark"] {
    --paper:#101210; --ink:#e9eae4; --muted:#9aa096; --rule:#2a2d28;
    --plate:#f7f7f4; --band:#181b18;
    --win:#4faf73; --off:#e0736a; --hid:#b07fd0;
  }
  :root[data-theme="light"] {
    --paper:#fbfbf9; --ink:#12140f; --muted:#63675f; --rule:#e2e4dd;
    --plate:#ffffff; --band:#f2f3ee;
    --win:#1b7837; --off:#c2453a; --hid:#7b3294;
  }

  body {
    background:var(--paper); color:var(--ink);
    font-family:var(--serif); font-size:17px; line-height:1.62;
    margin:0; padding:0 20px 96px;
    -webkit-font-smoothing:antialiased;
  }
  .wrap { max-width:66ch; margin:0 auto; }
  .wide { max-width:980px; margin:0 auto; }

  header { padding:72px 0 8px; }
  h1 {
    font-size:clamp(30px,5vw,44px); line-height:1.1; font-weight:600;
    margin:0 0 14px; letter-spacing:-.015em; text-wrap:balance;
  }
  .dek { font-size:19px; color:var(--muted); margin:0 0 22px; text-wrap:balance; }
  .byline {
    font-family:var(--sans); font-size:12px; letter-spacing:.09em;
    text-transform:uppercase; color:var(--muted);
    border-top:1px solid var(--rule); padding-top:14px;
  }

  h2 {
    font-family:var(--sans); font-size:12.5px; font-weight:600;
    letter-spacing:.13em; text-transform:uppercase; color:var(--muted);
    margin:60px 0 14px; padding-bottom:8px; border-bottom:1px solid var(--rule);
  }
  h3 { font-size:20px; font-weight:600; margin:34px 0 8px; letter-spacing:-.01em; }
  p { margin:0 0 16px; }
  strong { font-weight:600; }
  em { font-style:italic; }
  code {
    font-family:var(--mono); font-size:.85em;
    background:var(--band); padding:.12em .34em; border-radius:2px;
  }

  figure { margin:34px 0; }
  .plate {
    background:var(--plate); border:1px solid var(--rule);
    padding:14px; overflow-x:auto;
  }
  .plate img { display:block; width:100%; height:auto; min-width:520px; }
  figcaption {
    font-family:var(--sans); font-size:13px; line-height:1.5;
    color:var(--muted); margin-top:10px;
  }

  /* results band */
  .results { background:var(--band); border-top:1px solid var(--rule);
             border-bottom:1px solid var(--rule); margin:56px 0; padding:40px 20px; }
  .findings { display:grid; gap:22px; grid-template-columns:1fr; margin:0; padding:0; list-style:none; }
  @media (min-width:720px) { .findings { grid-template-columns:repeat(3,1fr); } }
  .finding { border-top:2px solid var(--ink); padding-top:12px; }
  .finding .n {
    font-family:var(--sans); font-size:11px; letter-spacing:.11em;
    text-transform:uppercase; color:var(--muted); display:block; margin-bottom:6px;
  }
  .finding .big {
    font-family:var(--mono); font-size:27px; font-variant-numeric:tabular-nums;
    letter-spacing:-.02em; display:block; margin-bottom:6px;
  }
  .finding p { font-size:15.5px; line-height:1.5; margin:0; color:var(--muted); }

  .tablewrap { overflow-x:auto; margin:28px 0; }
  table { border-collapse:collapse; width:100%; min-width:560px; font-size:15px; }
  th, td {
    text-align:right; padding:9px 12px; border-bottom:1px solid var(--rule);
    font-variant-numeric:tabular-nums;
  }
  th:first-child, td:first-child { text-align:left; font-family:var(--sans); font-size:13.5px; }
  thead th {
    font-family:var(--sans); font-size:12px; font-weight:600;
    letter-spacing:.05em; color:var(--muted); border-bottom:1.5px solid var(--ink);
  }
  tbody tr.key td { background:color-mix(in srgb, var(--band) 70%, transparent); font-weight:600; }
  td.win { color:var(--win); font-weight:600; }
  td.off { color:var(--off); font-weight:600; }
  .mono { font-family:var(--mono); font-size:.92em; }

  blockquote {
    margin:22px 0; padding:2px 0 2px 20px; border-left:2px solid var(--hid);
    font-style:italic; color:var(--ink);
  }
  blockquote cite {
    display:block; font-style:normal; font-family:var(--sans);
    font-size:12.5px; letter-spacing:.04em; color:var(--muted); margin-top:8px;
  }

  .note {
    font-size:15px; color:var(--muted); border-left:2px solid var(--rule);
    padding-left:18px; margin:26px 0;
  }
  footer {
    margin-top:64px; padding-top:18px; border-top:1px solid var(--rule);
    font-family:var(--sans); font-size:13px; color:var(--muted);
  }

  details.prompt { border-top:1px solid var(--rule); padding:14px 0; }
  details.prompt:last-of-type { border-bottom:1px solid var(--rule); }
  details.prompt > summary {
    cursor:pointer; list-style:none; font-family:var(--sans); font-size:14px;
    display:flex; align-items:baseline; gap:10px;
  }
  details.prompt > summary::-webkit-details-marker { display:none; }
  details.prompt > summary::before {
    content:"+"; font-family:var(--mono); color:var(--muted); font-size:15px;
  }
  details.prompt[open] > summary::before { content:"−"; }
  details.prompt > summary:focus-visible { outline:2px solid var(--hid); outline-offset:3px; }
  details.prompt .tag {
    font-size:11.5px; letter-spacing:.08em; text-transform:uppercase;
    color:var(--muted); margin-left:auto;
  }
  details.prompt pre {
    font-family:var(--mono); font-size:12px; line-height:1.5;
    background:var(--band); padding:14px 16px; margin:12px 0 0;
    overflow-x:auto; white-space:pre; border-left:2px solid var(--rule);
  }
  details.prompt.leak pre { border-left-color:var(--off); }
</style>

<div class="wrap">
  <header>
    <h1>Discovery or recall?</h1>
    <p class="dek">An evolutionary search appeared to discover the winning lines of
    tic-tac-toe on its own. We hid the answer and ran it again, then asked it to find
    something it could actually work out.</p>
    <p class="byline">Cheng-You Ho &nbsp;·&nbsp; Two experiments</p>
  </header>

  <p>Evolutionary search driven by a large language model is often reported to
  <em>discover</em> the structure of a problem. That claim is worth checking, because
  two very different things can produce it. A system that rediscovers structure it was
  shown is a search procedure with a good prior. A system that finds structure nobody
  supplied is something else entirely.</p>

  <p>We had a result of the first kind and mistook it for the second.</p>
</div>

<h2 class="wrap">The task</h2>
<div class="wrap">
  <p>Classify a tic-tac-toe board into one of three outcomes. The nine cells become
  nine <strong>qubits</strong>, and a search rewrites a <strong>quantum circuit</strong>
  that reads them. The circuit can join any three qubits with a
  <strong>three-qubit gate</strong>; there are 84 such triples to choose from.</p>

  <p>Eight of those 84 matter. The three rows, three columns and two diagonals are the
  <strong>winning lines</strong>, and they alone determine the answer. A search that
  puts its gates there has found the real structure of the task.</p>
</div>

<figure class="wide">
  <div class="plate"><img src="{fig_task}" alt="Board cells mapped to nine qubits, the eight winning lines, and the hardware connectivity graph."></div>
  <figcaption class="wrap" style="margin-left:auto;margin-right:auto;">
  The nine cells become nine qubits (a). The eight winning lines (b). The twelve
  qubit pairs the hardware permits, which follow grid adjacency (c).</figcaption>
</figure>

<div class="wrap">
  <h3>One structural fact drives everything</h3>
  <p>Because the wiring is grid adjacency, a row or column is a straight two-step walk
  and contains <strong>two</strong> permitted pairs. A diagonal steps diagonally twice
  and contains <strong>none</strong>. Rows and columns are visible in the wiring the
  model is shown. The two diagonals are not.</p>
</div>

<h2 class="wrap">The run that looked like a discovery</h2>
<div class="wrap">
  <p>A 100-generation search produced a circuit at 82.7% validation accuracy that placed
  all twelve of its three-qubit gates on winning lines, covering all eight. Across the
  whole run, <strong>916 of 916</strong> gates landed on winning lines. Not one
  exploratory error. All eight lines were present by generation five.</p>

  <p>That perfection is the tell. A search cannot sweep an 84-element space flawlessly
  in five moves. It was not searching, it was transcribing: the starter code it was
  shown defined <code>WIN_LINES</code>, <code>CORNERS</code> and <code>CENTER</code>
  outright, and the instructions named the game three times.</p>

  <p>The circuit signed its own confession. It named its parameters
  <code>zzz_rows</code>, <code>zzz_cols</code>, <code>zzz_diags</code>,
  <code>rot_corners</code>, <code>ry_center</code>, and tied all three rows to one
  shared parameter, which is the correct symmetry of tic-tac-toe. The anonymised runs
  below name theirs <code>zzz_023</code> and <code>crx_02</code>, by coordinate only.</p>

  <p class="note">Independent work by Baumann and Linnhoff-Popien reaches the same
  design deliberately, on the same task and wiring, and reports that motif-aligned
  gates are worth about +0.11 test accuracy. They describe it as a
  <em>task-informed</em> choice made by the designer. Our run reached that design with
  nobody deciding to supply it, then read the outcome as a discovery. The two are the
  same experiment under different labels.</p>
</div>

<h2 class="wrap">Hiding the answer</h2>
<div class="wrap">
  <p>We rebuilt the task so prior knowledge could not substitute for search. No task
  name, no geometric constants, no diagram, and a <strong>secret permutation</strong> of
  the qubit labels baked into the data and the wiring. The winning lines stay exactly as
  predictive, but they are no longer rows or columns of anything visible.</p>
</div>

<figure class="wide">
  <div class="plate"><img src="{fig_anonymize}" alt="The eight winning lines shown before and after the secret relabelling."></div>
  <figcaption class="wrap" style="margin-left:auto;margin-right:auto;">
  The same eight lines before and after relabelling. Obvious geometry becomes a
  scatter. Purple marks the two lines with no hardware link.</figcaption>
</figure>

<div class="wrap">
  <p>This creates the test that prior knowledge cannot pass. The two diagonals have no
  wiring to follow, so nothing visible points at them. They can be found
  <em>only</em> by noticing that circuits using them score better. We call these the
  <strong>hidden lines</strong>.</p>
</div>

<h2 class="wrap">What should count as chance</h2>
<div class="wrap">
  <p>The obvious baseline is that random placement hits a winning line 8/84 = 9.5% of the
  time. That baseline is wrong, and using it badly overstates the evidence.</p>
</div>

<figure class="wide">
  <div class="plate"><img src="{fig_strata}" alt="Triples grouped by hardware links, showing six of eight winning lines sit in the two-link group."></div>
  <figcaption class="wrap" style="margin-left:auto;margin-right:auto;">
  Six of the eight winning lines are exactly the triples carrying two hardware links.
  A preference for well-connected qubits alone hits a winning line 27.3% of the time.</figcaption>
</figure>

<div class="wrap">
  <p>So a model that merely favours well-connected triples, on ordinary engineering
  instinct and with no insight at all, looks like it is discovering. Every number below
  is reported against both baselines.</p>
</div>

<div class="results">
  <div class="wide">
    <h2 style="margin-top:0;">The results</h2>
    <ul class="findings">
      <li class="finding">
        <span class="n">Motif usage</span>
        <span class="big">100% &rarr; 39 / 0 / 7%</span>
        <p>With the answer supplied, every gate sat on a winning line. With it hidden,
        the three models scored 39%, 0%, and 7.4%. The last is below chance.</p>
      </li>
      <li class="finding">
        <span class="n">The decisive test</span>
        <span class="big" style="color:var(--off)">0 of 2</span>
        <p>No hidden line was found by any model. Every line they did touch was one
        with wiring to follow.</p>
      </li>
      <li class="finding">
        <span class="n">The motif was not needed</span>
        <span class="big">82.3%</span>
        <p>GPT-5.6-sol matched the leaked run's accuracy (82.7%) using
        <em>zero</em> winning lines.</p>
      </li>
    </ul>
  </div>
</div>

<div class="wide tablewrap">
  <table>
    <thead>
      <tr><th></th><th>Leaky<br><span style="font-weight:400">answer given</span></th>
      <th>Haiku 4.5<br><span style="font-weight:400">hidden</span></th>
      <th>Sonnet 5<br><span style="font-weight:400">hidden</span></th>
      <th>GPT-5.6-sol<br><span style="font-weight:400">hidden</span></th></tr>
    </thead>
    <tbody>
      <tr><td>Generations</td><td>100</td><td>30</td><td>30</td><td>30</td></tr>
      <tr><td>Gates on winning lines</td><td>916/916</td><td>35/89</td><td>0/46</td><td>7/95</td></tr>
      <tr><td>&nbsp;&nbsp;as a fraction</td><td>100%</td><td>39%</td><td>0%</td><td>7.4%</td></tr>
      <tr><td>p vs uniform (9.5%)</td><td class="mono">~10<sup>-935</sup></td><td class="mono">6.7e-14</td><td class="mono">1.00</td><td class="mono">0.81</td></tr>
      <tr><td>p vs connectivity (27.3%)</td><td class="mono">~10<sup>-517</sup></td><td class="mono">9.1e-3</td><td class="mono">1.00</td><td class="mono">1.00</td></tr>
      <tr><td>Distinct lines found</td><td>8/8</td><td>3/8</td><td>0/8</td><td>0/8</td></tr>
      <tr class="key"><td>Hidden lines found</td><td class="win">2/2</td><td class="off">0/2</td><td class="off">0/2</td><td class="off">0/2</td></tr>
      <tr><td>Proposals naming the game</td><td>92%</td><td>10%</td><td>27%</td><td>30%</td></tr>
      <tr><td>Best validation accuracy</td><td>82.7%</td><td>67.7%</td><td>72.0%</td><td><strong>82.3%</strong></td></tr>
      <tr><td>Best test accuracy</td><td>78.2%</td><td>65.5%</td><td>65.7%</td><td><strong>77.8%</strong></td></tr>
    </tbody>
  </table>
</div>

<div class="wrap">
  <p class="note">Haiku is the only arm with a positive signal, and most of it is the
  confound. It put 78% of its gates on well-connected triples, against 26% expected by
  chance. Measured honestly its result moves from p&nbsp;=&nbsp;6.7e-14 to
  p&nbsp;=&nbsp;9.1e-3, weaker by eleven orders of magnitude, and its single best circuit
  is not significant at all.</p>
</div>

<figure class="wide">
  <div class="plate"><img src="{fig_circuits}" alt="The best circuit from each run drawn as the triples its gates act on."></div>
  <figcaption class="wrap" style="margin-left:auto;margin-right:auto;">
  The best circuit from each run. Green is a gate on a winning line, red is off it.
  The leaked circuit covers the lines exactly; the others do not.</figcaption>
</figure>

<figure class="wide">
  <div class="plate"><img src="{fig_summary}" alt="Summary bars: gates on lines, coverage, and hidden lines found."></div>
  <figcaption class="wrap" style="margin-left:auto;margin-right:auto;">
  Only the run that was handed the answer passes the decisive test (c).</figcaption>
</figure>

<h2 class="wrap">How the models actually reasoned</h2>
<div class="wrap">
  <p>Every proposal carries a written rationale explaining the edit. Reading them settles
  the mechanism, and shows anonymisation worked only partly. Game vocabulary appears in
  92% of the leaked run's proposals, and still in 10&ndash;30% of the hidden ones.</p>
</div>

<figure class="wide">
  <div class="plate"><img src="{fig_vocab}" alt="Share of proposals using game vocabulary, by run and over generations."></div>
  <figcaption class="wrap" style="margin-left:auto;margin-right:auto;">
  The leaked run engages the game from its first edit and never stops. Anonymisation
  suppresses this without eliminating it.</figcaption>
</figure>

<div class="wrap">
  <p>GPT-5.6-sol reconstructed the task from the data alone, and said so:</p>

  <blockquote>
    an IQP-style feature extractor aligned to the eight winning lines of a 3x3 board
    &hellip; parameters shared across rows, columns, and diagonals
    <cite>GPT-5.6-sol, generation 9</cite>
  </blockquote>

  <p>That inference gives a clean test. A model that has <em>recalled</em> tic-tac-toe
  knows the lines in the standard layout, but the permutation moved them, so recalled
  lines are wrong. A model that has <em>discovered</em> them would hit the true ones.</p>
</div>

<figure class="wide">
  <div class="plate"><img src="{fig_recall}" alt="Gates on remembered versus true lines, and the score trajectory rejecting the recalled motif."></div>
  <figcaption class="wrap" style="margin-left:auto;margin-right:auto;">
  Across five generations it placed 8 of 8 gates on the lines of an <em>unpermuted</em>
  board and 1 of 8 on the true ones. Those attempts score below what it had already
  reached, and below its eventual best.</figcaption>
</figure>

<div class="wrap">
  <p>It proposed the remembered answer, measured it, watched it score 0.55 against the
  0.72 it had already achieved, and abandoned it. The loop worked exactly as a loop
  should. What it never did was find the structure on its own.</p>
</div>

<figure class="wide">
  <div class="plate"><img src="{fig_trajectory}" alt="Best-so-far score and motif usage across generations for all four runs."></div>
  <figcaption class="wrap" style="margin-left:auto;margin-right:auto;">
  The leaked run holds 100% motif usage from the start. The hidden runs hover near or
  below the connectivity baseline.</figcaption>
</figure>

<h2 class="wrap">A fairer test</h2>
<div class="wrap">
  <p>The test above may be unfair in one specific way. Winning lines are a
  <em>convention</em>: you either know the game or you don't, and no amount of staring
  at scrambled labels will yield them. A <strong>symmetry</strong> is different. It can
  be worked out from the shape of the data.</p>

  <p>So we ran two more tasks where the answer is a symmetry, built independently of
  everything above. In the first, each record says which of the 28 possible connections
  among eight dots are present, and the label depends only on the shape of the network,
  not on which dot is called which. <strong>Renaming the dots cannot change the
  answer.</strong> In the second, all inputs are quantum states that look the same from
  every direction.</p>

  <p>Neither task mentions symmetry, invariance, permutation or spin anywhere in its
  instructions or starter code. We grepped for all of them. And both let gates act on
  any pair, so the connectivity confound doesn't arise.</p>

  <h3>The model worked it out</h3>
  <p>At generation 33, GPT-5.6-sol proposed a circuit it named
  <code>permutation_equivariant_ansatz</code>:</p>

  <blockquote>
    Exploit the likely graph structure of the 28 binary features, which correspond
    exactly to all unordered pairs of eight qubits &hellip; rotation parameters are
    shared across all qubits, and CZ gates cover the complete graph. This aligns the
    circuit with relabeling-invariant graph classification.
    <cite>GPT-5.6-sol, generation 33</cite>
  </blockquote>

  <p>That is a derivation, not a memory. 28 is the number of pairs of 8 things, so the
  data are networks; a network's label can't depend on names; therefore treat all eight
  identically. It then built exactly that, and the score paid for it.</p>
</div>

<figure class="wide">
  <div class="plate"><img src="{fig_symmetry}" alt="Symmetry of proposed circuits over generations, the score before and after, and accuracy against parameter count."></div>
  <figcaption class="wrap" style="margin-left:auto;margin-right:auto;">
  Symmetry jumps to exact at generation 33 and stays (a). The score jumps with it (b).
  Across models, more symmetric circuits use fewer parameters and score higher (c).</figcaption>
</figure>

<div class="wide tablewrap">
  <table>
    <thead>
      <tr><th></th><th>test accuracy</th><th>parameters</th><th>symmetry</th></tr>
    </thead>
    <tbody>
      <tr><td>starting circuit</td><td>86.7%</td><td>146</td><td>0.15</td></tr>
      <tr><td>Sonnet 5</td><td>92.0%</td><td>98</td><td>0.18</td></tr>
      <tr><td>Haiku 4.5</td><td>92.0%</td><td>38</td><td>0.66</td></tr>
      <tr class="key"><td>GPT-5.6-sol</td><td class="win">96.0%</td><td>26</td><td class="win">0.96</td></tr>
    </tbody>
  </table>
</div>

<div class="wrap">
  <p class="note">The second task told us nothing. All three models hit 100% accuracy
  within nine generations, so it saturates before circuit design can matter. It needs to
  be made harder before it can test anything.</p>
</div>

<h2 class="wrap">What this means</h2>
<div class="wrap">
  <p><strong>What you can deduce, it finds. What you can't, it doesn't.</strong> The two
  experiments gave opposite results from the same model in the same week, and the
  difference isn't capability. Winning lines can't be deduced from scrambled labels, so
  the model fell back on memory and was wrong. Permutation symmetry <em>can</em> be
  deduced from the shape of the input, so it reasoned it out and was right. Both times
  the score had the final word.</p>

  <p><strong>The search did not discover the motif.</strong> Usage collapsed once the
  answer was removed, the three models disagree with each other, most of the surviving
  signal is a connectivity preference unrelated to the task, no arm passed the hidden-line
  test, and the one model that reconstructed the domain was corrected by the score.</p>

  <p><strong>But the positive result is narrower than "discovery".</strong> The model
  generated the symmetry hypothesis by reasoning about the task description, and the
  score then confirmed it. That's hypothesis generation plus validation, not blind
  search. It is a weaker claim, and a more useful capability, because it is how the loop
  would actually be used.</p>

  <p><strong>The motif is good structure, but not the only route.</strong> Independent
  work on this exact task &mdash; same nine qubits, same wiring, same eight winning
  triples &mdash; finds that adding motif-aligned gates to a symmetric circuit lifts test
  accuracy from about 0.69 to about 0.80, the largest single gain measured. So the motif
  genuinely works. What our result removes is the inference from <em>this circuit uses
  the motif</em> to <em>this search found the motif</em>, since a circuit that never
  used it scored just as well.</p>

  <p><strong>Concealment is weaker than distortion.</strong> Removing the name and the
  constants did not stop a capable model from recovering the domain. What saved the
  experiment was the permutation, which made recalled knowledge produce a specific,
  checkable, wrong answer. Designing controls so prior knowledge fails <em>visibly</em>
  beats trying to prevent it.</p>

  <p class="note"><strong>What this does not show.</strong> The hidden arms ran 30
  generations against the leaked run's 100, a budget limit rather than a design choice.
  This rules out fast discovery of this motif by these models. It does not rule out slow
  discovery. The leaked run also used three proposer models against one per hidden arm,
  so that comparison is between protocols, not matched models.</p>
</div>

<h2 class="wrap">What we actually told the model</h2>
<div class="wrap">
  <p>Every claim above about what the model was and wasn't told rests on these
  texts. They are the task messages exactly as sent, at every generation. Nothing
  else describes the problem to the model: the only other inputs are the starter
  program and the score from each evaluation. Open them and check.</p>

  <details class="prompt">
    <summary>Scrambled tic-tac-toe task<span class="tag">no game named</span></summary>
    <p style="font-size:15px;color:var(--muted);margin:10px 0 0;">Search it for
    “tic-tac-toe”, “board”, “row”, “column”, “diagonal”, “corner”, “centre” or
    “winning”. None appear. It does give the qubit wiring, because that limits which
    circuits are legal.</p>
    <pre>{MOTIF}</pre>
  </details>

  <details class="prompt">
    <summary>Network task<span class="tag">no symmetry named</span></summary>
    <p style="font-size:15px;color:var(--muted);margin:10px 0 0;">Search it for
    “symmetry”, “permutation”, “invariant”, “equivariant”, “group” or “graph”. None
    appear. It never says the 28 features are the pairs of 8 qubits: the model had to
    work that out.</p>
    <pre>{SN}</pre>
  </details>

  <details class="prompt">
    <summary>Quantum-state task<span class="tag">no symmetry named</span></summary>
    <p style="font-size:15px;color:var(--muted);margin:10px 0 0;">Search it for
    “spin”, “SU(2)”, “rotation”, “Heisenberg” or “singlet”. None appear. The inputs
    are described only as “a precomputed 8-qubit state vector”.</p>
    <pre>{SU2}</pre>
  </details>

  <details class="prompt leak">
    <summary>For contrast: what the leaked run was shown<span class="tag">the answer, outright</span></summary>
    <p style="font-size:15px;color:var(--muted);margin:10px 0 0;">This sits at the top
    of the original run's starter file, above the editable region, so it went into the
    model's context in full every generation.</p>
    <pre>{LEAKY}</pre>
  </details>
</div>

<div class="wrap">
  <footer>Four motif runs and five symmetry runs on the Yale Bouchet cluster ·
  ShinkaEvolve · secret permutation seed 777</footer>
</div>
"""

out = HTML
for name, uri in FIGS.items():
    out = out.replace("{" + name + "}", uri)
for name, text in PROMPTS.items():
    out = out.replace("{" + name + "}", text)
OUT.write_text(out)
kb = OUT.stat().st_size / 1024
print(f"wrote {OUT} ({kb:.0f} KB)")
