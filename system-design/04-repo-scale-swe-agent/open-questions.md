# Open questions - 04 Repo-scale SWE agent

This case has the thinnest evidence base of the filled cases in the library, and
the largest gap sits directly under its headline claim. Four of the twelve
dimensions are effectively unanswered.

## Unknown mechanism

- **What is the agent-computer interface?** The paper's title asserts that
  agent-computer interfaces enable automated software engineering, and our
  material contains the claim without the design. This is the largest gap in the
  case, because the thesis is precisely that this component is decisive. Without
  it, dimension 5 states a principle and describes nothing. Reading the paper
  itself would answer it, and until then this case cannot be used as a source on
  interface design.

- **How is resolution actually determined?** Our reading throughout is that
  paired pull requests supply a machine-checkable criterion, which is the premise
  the entire case rests on. Our material states how instances were drawn and not
  how a candidate edit is judged. This matters more than any other open question
  here, because if the criterion were partly human or partly heuristic, the
  contrast with case 03 that justifies this case would weaken. The benchmark's
  evaluation procedure would answer it.

- **What bounds the loop?** We infer a loop from the requirement to interact with
  execution environments, and we have no step limit, no retry policy, and no stop
  condition. This matters because case 03's most-reported failure was an
  unbounded loop, and we cannot say whether this system has the same exposure. A
  description of the control loop would answer it.

- **How does the agent select what to read from a repository?** A codebase
  exceeds any context window, so a selection strategy exists. Whether it is
  search, static analysis, directory traversal, or model-directed navigation is
  unknown. This matters because dimension 3 argues that selection quality is the
  design problem here, and we cannot say how this system solves it. The paper's
  method section would answer it.

- **Is there any state that survives between attempts on one instance?**
  Dimension 7 is empty. This matters because an agent that remembers a failed
  hypothesis behaves very differently from one that restarts clean after each
  test run. A description of the agent's memory, if any, would answer it.

## Unknown magnitude

- **What does one instance cost to attempt?** No token, time, or money figure
  appears in our material, so dimension 12 reports nothing. This matters because
  the practicality of the retry-until-tests-pass shape depends entirely on what
  a retry costs. Per-instance cost accounting would answer it.

- **How often does the oracle get gamed?** We name overfitting to the oracle as a
  reasoned failure mode and have no measurement of it. This matters because it
  is the specific risk created by the property that makes this case attractive.
  An analysis comparing test-passing edits against human-judged correct edits
  would answer it.

- **How large is a typical instance?** Repository size, issue length, and the
  number of files a correct patch touches are all unstated beyond the
  qualitative claim that changes frequently span multiple functions, classes,
  and files. This matters for anyone trying to reproduce the setup at a
  different scale.

## Disputed between sources

None. Both sources are first-party papers by overlapping author groups and they
are used here only for claims each states directly. No outside analysis has been
consulted, which means nothing in this case has been independently checked.

## Deliberately out of scope

- **Whether SWE-bench is a good benchmark.** Critiques of benchmark validity are
  a research conversation. This library records what the benchmark is and how
  its construction shapes the archetype. The paper topic `07-evaluation` in the
  sibling paper repository is the place for the critique.

- **How other systems score on SWE-bench.** Comparative results are not in our
  material and are not what this case is for. The case studies an archetype, not
  a leaderboard.

- **Whether the oracle property transfers to other languages or ecosystems.** Our
  material describes Python repositories. Generalizing beyond that is a question
  for whoever builds the equivalent set elsewhere, and the "one thing to steal"
  section already frames the construction as a recipe to be re-run rather than a
  result to be inherited.
