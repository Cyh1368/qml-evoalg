# Bibliography audit (2026-11-11)

Every entry of `research/paper/main.tex` was checked against a **primary** record: the
arXiv Atom API (`https://export.arxiv.org/api/query?id_list=...`), Crossref
(`https://api.crossref.org/works/<doi>`) for journal metadata, or the PMLR proceedings
page. Raw lookups are reproduced below. **All eight entries contained at least one
material error**; the two the referee flagged are confirmed, and six more were found.

| key | manuscript said | verified primary record | errors |
|---|---|---|---|
| `meyer2023` | "Symmetry-generalised ansätze and invariant re-uploading for quantum machine learning", J. Meyer, M. Berkemer, M. Bretz, et al., PRX Quantum 4:010328 (2023) | **J. J. Meyer, M. Mularski, E. Gil-Fuster, A. A. Mele, F. Arzani, A. Wilms, J. Eisert, "Exploiting Symmetry in Variational Quantum Machine Learning", PRX Quantum 4, 010328 (2023)**, doi:10.1103/PRXQuantum.4.010328 | title invented (no such title exists for this DOI; the co-author list is wrong); the "invariant re-uploading" phrase it supported is not supported by this source and is removed from the text |
| `nguyen2024` | "General constructive prescriptions for equivariant quantum neural networks", Q. H. Nguyen, A. Garcia, B. O'Gorman, et al., PRX Quantum 5:020330 (2024) | **Q. T. Nguyen, L. Schatzki, P. Braccia, M. Ragone, P. J. Coles, F. Sauvage, M. Larocca, M. Cerezo, "Theory for Equivariant Quantum Neural Networks", PRX Quantum 5, 020328 (2024)**, doi:10.1103/PRXQuantum.5.020328 (arXiv:2210.08566) | title, authors and article number all wrong; the cited number **020330 is an unrelated paper** ("High-Order Randomized Compiler for Hamiltonian Simulation", Nakaji, Bagherimehrab & Aspuru-Guzik, PRX Quantum 5, 020330) |
| `mansky2025` | "Permutation-invariant quantum machine learning for graph properties with approximate symmetry", A. Mansky, Z. Wang, T. H. Hsieh, arXiv:2505.12764 | **M. B. Mansky, T. Rohe, G. Stenzel, A. Bravo de la Serna, S. Londoño Castillo, G. Sathish, D. Nikolaidou, D. Bondarenko, L. Menzel, C. Linnhoff-Popien, "Solving graph problems using permutation-invariant quantum machine learning", arXiv:2505.12764 (2025)**, submitted to QCE 25 | title, author initials and co-author list wrong; "approximate symmetry" is not in the record and is dropped from the text |
| `baumann2026` | "Subgroup sharing and task-aligned interactions in quantum tic-tac-toe", L. Baumann and C. Linnhoff-Popien, arXiv:2606.20316 | **M. Baumann, C. Linnhoff-Popien, J. Stein, "Symmetry Alone Is Not an Ansatz: Task-Aligned Interactions in Equivariant Quantum Circuits", arXiv:2606.20316 (2026)**, accepted at the 4th International Workshop on QML (IEEE QCE26) | title wrong, first author's initial wrong (M. not L.), third author omitted, venue omitted |
| `elesedy2021` | "Provably depth-efficient quantum neural networks via symmetric architecture", A. Elesedy and A. R. Zaidi, ICML, PMLR 139 (2021) | **B. Elesedy and S. Zaidi, "Provably Strict Generalisation Benefit for Equivariant Models", ICML 2021, PMLR 139** (proceedings.mlr.press/v139/elesedy21a.html; arXiv:2102.10333) | title invented, both author initials wrong (Bryn Elesedy, Sheheryar Zaidi) — the referee's finding, confirmed |
| `otto2023` | "Symmetry breaking and restoration in variational quantum circuits via Lie derivatives", D. Otto, Y. Chen, C. Tomesh, et al., arXiv:2311.00212 (2023) | **S. E. Otto, N. Zolman, J. N. Kutz, S. L. Brunton, "A Unified Framework to Enforce, Discover, and Promote Symmetry in Machine Learning", arXiv:2311.00212 (2023); J. Mach. Learn. Res. 26(248):1–83 (2025)** | title invented, authors invented, and the now-published JMLR version was not cited |
| `chen2026` | "Task-level quantum symmetry discovery: finite-measurement inference, task validation and projection bias", Y. Chen, arXiv:2610.00157 (2026) | **Z. Chen, "Symmetry Discovery in Quantum Learning: Observable-Level and Task-Level Inference from Finite Measurements", arXiv:2610.00157 (2026)** | title paraphrased rather than quoted, author initial wrong (Zeyu) |
| `lange2026` | "ShinkaEvolve: bandit ensemble selection and novelty rejection for LLM-driven program evolution", R. Lange, C. Im, S. Toneva, ICLR 2026 | **R. T. Lange, Y. Imajuku, E. Cetin, "ShinkaEvolve: Towards Open-Ended and Sample-Efficient Program Evolution", arXiv:2509.19349 (2025)** (52 pages, 14 figures; no journal/venue record) | title, authors and year wrong; the "ICLR 2026" venue is unverifiable and removed; **"bandit ensemble selection" is not from this paper** — the UCB ensemble is the in-house prior study's own harness modification, and the text now attributes it there |

## Claim-level check (beyond metadata)

* `meyer2023` is now cited only for "exploiting symmetry in variational QML"; the
  specific "invariant re-uploading" claim was removed because the verified source does
  not carry it.
* `lange2026` is now cited for the LLM-evolutionary harness (parent sampling, novelty
  rejection, sample efficiency) and **not** for bandit model selection, which belongs to
  the audited in-house study.
* `mansky2025` is cited for permutation-invariant QML on graph problems (connectedness),
  which the verified title supports; the "approximate symmetry" qualifier is removed.
* `baumann2026` supports "symmetry alone does not determine a useful architecture" — the
  verified title ("Symmetry Alone Is Not an Ansatz") supports this more directly than the
  invented one did.

## The audited prior study is now cited explicitly

The audited study is **an earlier version of this project by the same author**:
Cheng-You Ho, "Identifying Symmetries in Quantum Machine Learning with LLM-Guided
Evolutionary Search", 31 Aug 2026, archived in this repository as `README.md` at git
commit `13ea13eb76af2f587c508aefde81b9dd026b3ce1`, with run artifacts under
`experiments/transfer-sn/` and `analysis/` and the audit script `research/audit.py`.
It is cited as an archived artifact (`ho2026prior`) rather than described anonymously,
and the paper states that it is self-auditing.

## Reproduce this audit

```bash
for id in 2509.19349 2210.08566 2505.12764 2311.00212 2606.20316 2610.00157 2102.10333; do
  curl -sS "https://export.arxiv.org/api/query?id_list=$id" | grep -E "<title>|<name>|<published>|journal_ref"
done
for d in 10.1103/PRXQuantum.4.010328 10.1103/PRXQuantum.5.020328 10.1103/PRXQuantum.5.020330; do
  curl -sS "https://api.crossref.org/works/$d" | python3 -m json.tool | head -40
done
curl -sS https://proceedings.mlr.press/v139/elesedy21a.html | grep -i "<title>"
```

## Round-2 re-check (2026-11-11T22:40Z): one of *my own* audit corrections was wrong

The second-round referee wrote that "Meyer et al. explicitly discuss invariant reuploading
constructions; the rebuttal's blanket assertion that this attribution was unsupported should
be revisited against the primary text." **They are right and my round-1 audit line was
wrong.** I re-read the primary text, not an abstract: the open-access accepted manuscript
retrieved from APS (`http://harvest.aps.org/v2/journals/articles/10.1103/PRXQuantum.4.010328/fulltext`,
doi:10.1103/PRXQuantum.4.010328, Crossref-confirmed as Meyer, Mularski, Gil-Fuster, Mele,
Arzani, Wilms & Eisert, *Exploiting Symmetry in Variational Quantum Machine Learning*, PRX
Quantum 4, 010328 (2023), published 2023-03-17). Verbatim, from that file:

> "we show how these building blocks can be combined to construct variational quantum **data
> re-uploading models that make invariant predictions** and thus include a meaningful
> inductive bias" (Sec. IV, opening)

> "Because of the no-cloning theorem, it is important for the expressivity of quantum
> learning models to embed the data into the quantum circuit multiple times, a process
> dubbed **data re-uploading** [35–37]."

> "**Definition 1 (Equivariant embedding).** We call a data encoding unitary U(x) equivariant
> with respect to the data symmetry V_s if U(V_s[x]) = U_s U(x) U_s†."

> "**Proposition 2 (Twirling formula).** … T_U[X] = (1/|S|) Σ_{s∈S} U_s X U_s† defines a
> projector onto the set of operators commuting with all elements of the representation",
> applied to give the equivariant gateset T_U[G] = {T_U[G] | G ∈ G}.

> "As our main contribution, we show how to embed data in a way that enables us to build
> **invariant learning models** for which we give both a general blueprint and mathematical
> tools for their design."

Consequences, applied in the manuscript:

1. The audit row for `meyer2023` above is **superseded** on this point: the bibliographic
   correction (title, authors, article number) stands, but the claim that the source does not
   support invariant re-uploading is withdrawn. It was wrong, and it was the kind of error a
   citation-only check produces: I verified the *record*, then reasoned about the *content*
   from memory.
2. The related-work text now states plainly that Meyer et al. already provide (i) equivariant
   data encodings, (ii) the twirling/Reynolds projector onto the commutant as a gate- and
   ansatz-symmetrisation tool, and (iii) a blueprint for invariant prediction with re-uploading
   models. Our constructive equivariant baseline is an instance of their blueprint, and our
   inference-time average is the **output-side** specialisation of their Proposition 2.
3. That narrows what this paper may claim. The averaging operator, the projection identity and
   the invariant-model blueprint are not our contributions. What is left, and what the revised
   contribution table now says, is the **measurement**: how much of the benefit a
   label-preservation verifier actually gates, on which targets it is vacuous, and what a
   verifier-free defect gate achieves instead (Addendum A5.2–A5.4).
