# Notes on Labelling circuits

In this repository, we investigate running ShinkaEvolve on a graph connectedness problem involving 8 qubits. The key symmetry in this problem is S8. Thus, the optimal answer should be one that utilizes the symmetry (by, for example, using 28 CZ gates to tie all pairs of the 8 qubits).

There are 3 model ensembles:
- Frontier @ xhigh: GPT 5.6 Sol, Claude Opus 4.6, Gemini 3.1 Pro
- Mid @ medium: GPT 5.4 Mini, Gemini 3 Flash, Claude Haiku 4.5
- Weak @ low: GPT 5.4 Nano, Gemini 3.1 Flash Lite, Qwen3 Coder

We have a lot of ShinkaEvolve runs in this repository. Here are the ones that I am most interested about:

- The `or` runs use different ensembles and tackle the same graph connectedness problem.
- The `frw3` runs which continued the evolution after generation 3 of frontier models. This includes 10 runs by weak models, 10 by mid tier models, and another 4 by the original frontier models, as well as 5 from the frontier models without. GPT which proposed the best solutions.

For each run, we wanted to know whether the ensemble is capable of identifying the symmetry and actually building it. Thus, we should apply labels to each circuit. Each circuit is composed of several different parts and they can be grouped by the parameter that they share. Therefore, we can break each circuit into different parts. For example, one part could be all the gates sharing one rotation parameter theta_star, and if these gates happen to all be CRY, then we can hypothesize that the ensemble has figured out that it might be good to apply a constant rotation across the qubits. Note that gates like CZ do not take any rotation angles, so it may be hard to classify them. However, You should try to separate the circuit into layers. The first layer might be doing CRX rotations, the second might be a sequence of CZ, followed by CY, and the last might be some CZ. Notice that if we just group all the CZ together, then it might be very messy because although the second layer and the fourth layer might have some structure independently, when added together, they might look noisy. So we should never analyze a bunch of gates from different layers together, although they might be the same gates. The second layer might be trying to tie all the qubits together, while the final layer might be only trying to tie some key qubits together, and they should be separately discussed.

In short, it is very important that you figure out a way to analyze each circuit and break it into layers. Each layer should contain a similar pattern.

After each circuit is decomposed into layers, we look at each layer and figure out whether that layer has any inherent symmetries. This includes the following labels:

- all-singular: The same set of gates are applied on all eight of the qubits individually. This only applies to single qubit gates.
- all-double: The same set of two-bit gates apply to all 28 possible pairings of the 8 cubic gates.
- mirror: The gates applied follow some sort of mirror symmetry, like a CZ gate applied on qubits i and qubits 7-i.
- (If you identify more symmetries in your analysis, you may continue adding them.)
- none: None of the above.

After we analyze each circuit and identify the symmetry in each layer, we can classify a circuit based on what symmetry it exhibits. It is sufficient to say that a circuit has all-double symmetry if at least one layer has it. This is valid because if there is one layer in the circuit that identifies the symmetry, then the other layers don't necessarily need to exhibit this, since they might be just processing the data in some other way.

After all the circuits are labeled, look at each ensemble's performance under each setting (forward after gen 3 or from scratch). For each ensemble and each setting, how often does it exhibit a particular kind of symmetry? What is the score that each circuit gets if it satisfies a particular symmetry?

Generate a detailed HTML file to answer this. Make sure all your numbers contain uncertainties and that all numbers are derived from statistical methods. Make sure all your claims are grounded in evidence. Use simple English. Do not assume the reader has any context about this project. 