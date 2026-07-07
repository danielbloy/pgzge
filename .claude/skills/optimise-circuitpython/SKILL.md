---
name: optimise-circuitpython
description: Analyze and optimise code under pmpge/ for CircuitPython/MicroPython performance (speed first, memory second) without breaking the Pygame Zero desktop path. Use when asked to optimize, profile, speed up, or reduce RAM/allocations in the engine, or to review update()/draw() hot-path performance for microcontrollers.
---

# Optimise pmpge for CircuitPython

This skill reviews and improves code in `pmpge/` for running on constrained
microcontrollers (CircuitPython/MicroPython), per the performance targets in
`devices/README.md` (30 fps @ 160x120, 20-50 GameObjects, 8x8/16x16 sprites).
**Speed is the primary objective, memory is secondary** — an optimisation that
trades a little extra RAM for a meaningfully faster hot path is a good trade;
the reverse usually is not, unless RAM pressure is the actual bottleneck being
reported.

## Non-negotiable constraint

Every file under `pmpge/` must keep running **unmodified** on both desktop
(Pygame Zero) and CircuitPython/MicroPython — this is the whole point of the
engine (see CLAUDE.md). Never propose a fix that:

- Uses CPython-only stdlib (`typing`, `collections.abc`, `importlib`,
  `dataclasses`, f-string `=` debugging, etc.) outside an
  `is_running_on_desktop()` guard, matching the existing pattern in
  `pmpge/game_object.py` and `pmpge/environment.py`.
- Changes a public method signature or trait contract without updating every
  caller in `pmpge/`, `tests/`, `examples/`, and `games/`.
- Adds a dependency not already vendored for the microcontroller target.

If a genuinely good optimisation would break this, say so and stop rather than
applying it — flag it as a design question for the user instead.

## Readability constraint

Speed and memory are not the only objectives — **readability must be
preserved**. This is a teaching engine for Code Clubs (see CLAUDE.md); code
that's fast but unreadable works against the project's actual goals. Concretely:

- **Every non-obvious optimisation must carry a comment explaining why.** If
  the optimised form isn't self-evidently doing the same thing as the naive
  form a reader would expect, add a short comment stating the reason (e.g.
  "cached locally to avoid re-resolving `math` global every frame", "unit is
  thousandths-of-a-pixel/sec to keep this integer math on devices without an
  FPU"). This follows the same "comment the WHY, not the WHAT" rule as the
  rest of the codebase — the difference is that for a deliberate optimisation,
  the non-obviousness is usually guaranteed, so check for a comment before
  considering a fix finished, don't skip it.
- If an optimisation can't be made readable even with a comment (e.g. it
  requires unrolling a loop or hand-inlining a call chain), prefer the more
  readable, slightly-slower version unless the speed gain is large and
  measured. When reporting such a finding, say so explicitly and let the user
  decide the trade-off rather than defaulting to the faster form.
- This applies retroactively too: if the checklist review turns up an
  *existing* optimisation in `pmpge/` that isn't commented (e.g. a cache-to-local
  pattern with no explanation), flag adding the missing comment as a (very
  low-risk) finding in its own right, separate from any new change.

## Process

1. **Scope**: default to all of `pmpge/` excluding `pmpge/drivers/*/pgzero.py`
   (desktop-only, never runs on-device — deprioritize). If the user names a
   file/folder, scope to that instead.
2. **Classify before judging.** For each candidate change, classify the code as:
    - **Hot path**: anything reachable from `update_hierarchy()` /
      `draw_hierarchy()` every frame — `GameObject.update()`/`draw()`, trait
      `update()`/`draw()` methods (`pmpge/traits/*.py`), `RateLimiter.__call__`,
      driver `update()`/`draw()` implementations.
    - **Cold path**: setup/teardown — `GameObject.__init__`, `apply_trait()`
      (uses `dir()` + reflection, but only runs once per GameObject creation),
      driver `init()`/`deinit()`, `import_config()`.
      Speed fixes only matter in the hot path — don't "optimise" cold path code at
      the cost of readability, since it buys nothing at 30 fps. Memory fixes
      matter in both, but per-instance state that's duplicated across every
      GameObject (hot *and* persistent) matters most.
3. **Apply the checklist** in `references/checklist.md` to the scoped files.
   It's grounded in this codebase's actual hot paths, not generic advice.
4. **Report findings before changing anything**, ranked speed-impact first
   then memory-impact, each with:
    - `file:line`, hot/cold classification
    - the concrete failure/cost scenario (e.g. "allocates 2 new lists per
      GameObject with children on every update() call where nothing died")
    - a proposed before/after snippet
    - any risk to the desktop/microcontroller parity constraint above
5. **Only apply fixes the user confirms.** After applying, you MUST reproduce
   the CI sequence from CLAUDE.md before calling it done:
   ```
   flake8 pmpge --count --select=E9,F63,F7,F82 --show-source --statistics
   pytest tests/
   pytest examples/
   PYTHONPATH=. python validate/validate_all.py
   ```
   Note the honest limit here: none of this measures actual frame rate on
   real hardware. `validate/validate_all.py` only runs the non-interactive
   subset on desktop as a smoke test. If the user wants a real before/after
   comparison, point them at `validate/validation.md` (device setup) and
   `validate/performance/README.md` (results log) — that step needs real
   hardware and a human, not this skill.
6. **If a fix generalizes beyond this one review**, offer to add it to the
   "Optimisation roadmap" in `validate/performance/README.md` so it's tracked
   in one place instead of scattered across memory/PRs. Don't duplicate that
   file's content into this skill — read it fresh each time, since it's a
   living document that changes independently of this skill.

## Output format

Report only — do not silently rewrite files. Structure like this:

```
## Speed

1. [HOT] pmpge/game_object.py:561-565 — update_hierarchy() rebuilds two list
   comprehensions per GameObject-with-children on every call where
   `something_destroyed` is True, even if none of *that* object's children
   died.
   Cost: O(children) allocation × every parent GameObject, every frame a
   destroy happened anywhere in the tree.
   Fix: <snippet, with a comment explaining the non-obvious part>
   Desktop/CP parity risk: none — pure Python, no platform-specific API.
   Readability: comment added at the changed line / no comment needed because
   the change is self-evident / not readable enough even with a comment — see
   note.

## Memory

1. [COLD] ...
```

Then ask which findings to apply before touching any file.
