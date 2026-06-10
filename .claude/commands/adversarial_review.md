Run /codex:adversarial-review on the current branch diff vs main (or HEAD~1 if on main).

Context for Codex:
- This is a paper-only TAR trading research system. No live broker connections.
- Gate logic in src/tar_system/scoring/gates.py is the authority. Multi-agent scorer is advisory only.
- Flag any change that: bypasses a scoring gate, modifies verdict logic, touches file I/O with user input, or could accidentally enable live trading.
- KEEP/REVIEW/KILL verdict changes are high risk — scrutinise those paths hardest.
- Focus on: logic correctness, security (path traversal, injection), data integrity, unintended side effects.
