"""Generate appendix.tex verbatim from the prompts actually sent to the models."""
import re
from pathlib import Path

SP = Path(__file__).resolve().parent
OUT = Path.home() / "QuantumAnsatz/qml-ea/tic-tac-toe/paper-anon-motif/appendix.tex"

raw = (SP / "prompts.txt").read_text()
blocks = {}
for tag in ("MOTIF", "SN", "SU2"):
    m = re.search(r"<<<<<<<<<<%s\n(.*?)\n>>>>>>>>>>%s" % (tag, tag), raw, re.S)
    blocks[tag] = m.group(1).strip("\n") if m else "(missing)"
leaky = (SP / "leaky_seed.txt").read_text().strip("\n")

# words a reader may want to search for; we assert none appear
FORBIDDEN_MOTIF = ["tic-tac-toe", "board", "row", "column", "diagonal",
                   "corner", "centre", "center", "winning", "win line"]
FORBIDDEN_SYM = ["symmetr", "equivar", "invaria", "permut", "orbit",
                 "group", "S_8", "SU(2)", "spin", "Heisenberg", "isotropic",
                 "connected", "graph", "singlet"]


def check(text, words):
    low = text.lower()
    return [w for w in words if w.lower() in low]


hits_motif = check(blocks["MOTIF"], FORBIDDEN_MOTIF)
hits_sn = check(blocks["SN"], FORBIDDEN_SYM)
hits_su2 = check(blocks["SU2"], FORBIDDEN_SYM)

body = r"""
\appendix
\section{The exact instructions given to the proposer}
\label{app:prompts}

Every claim in this paper about what the model was and was not told rests on the
text below. These are the task messages verbatim, as sent to the proposer at
every generation, reproduced in full so the reader can check them rather than
take our word for it. Nothing else describes the task to the model: the only
other inputs are the seed program, the formal gate schema included below, and the
numerical feedback from each evaluation.

\subsection{Anonymised motif task (Sections 5--6)}

The claim is that this text never names tic-tac-toe and never mentions boards,
rows, columns, diagonals, corners, centres or winning lines. It does disclose the
qubit connectivity, because that constrains which circuits are legal, and it does
name the readout groups, which is the intentional partial-symmetry disclosure
discussed in Section~\ref{sec:anon}.

\begin{lstlisting}[style=prompt]
%s
\end{lstlisting}

\subsection{Network task (Section~\ref{sec:sym}, task A)}

The claim is that this text never mentions symmetry, permutation, invariance,
equivariance, orbits, groups, or graphs, and never states that relabelling the
qubits leaves the label unchanged. The word ``pair'' appears only to define the
feature map. That $28 = \binom{8}{2}$, and therefore that the records are graphs,
is something the model must work out; it is stated nowhere.

\begin{lstlisting}[style=prompt]
%s
\end{lstlisting}

\subsection{Quantum-state task (Section~\ref{sec:sym}, task B)}

The claim is that this text never mentions spin, SU(2), rotation invariance,
isotropic exchange, the Heisenberg model, singlets or dimerisation. The inputs
are described only as ``a precomputed 8-qubit state vector''. The one
non-neutral statement is that the score rewards parameter economy, which is a
property of the fitness function and not a hint about which structure achieves
it.

\begin{lstlisting}[style=prompt]
%s
\end{lstlisting}

\subsection{For contrast: what the leaked run was shown}

The following sits at the top of the seed program of the original run
(Section~\ref{sec:leaky}), above the editable region, and is therefore included
in the proposer's context in full at every generation. It is reproduced to make
the difference between the two conditions concrete.

\begin{lstlisting}[style=prompt]
%s
\end{lstlisting}

\noindent The eight winning lines are listed outright, together with the board
geometry, the corner and centre roles, and an ASCII diagram of the grid. No
search was required to recover any of it.
""" % (blocks["MOTIF"], blocks["SN"], blocks["SU2"], leaky)

OUT.write_text(body.lstrip("\n"))
print("wrote", OUT)
print("automated leak check (should all be empty):")
print("  motif task, game words :", hits_motif)
print("  network task, sym words:", hits_sn)
print("  state task, sym words  :", hits_su2)
