---
name: circuitpython-performance-analysis
description: "Analyse and optimise Python code in the pmpge/ directory for CircuitPython. Use when: reviewing performance, reducing memory allocations, optimising hot paths, improving update/draw loop speed, checking for memory leaks, profiling game engine code, CircuitPython speed optimisation, microcontroller performance. Optimises for speed first then memory. Readability is preserved — all non-obvious optimisations are commented."
argument-hint: "file or module to analyse (e.g. pmpge/game_object.py), or 'all' to scan the whole pmpge/ directory"
---

# CircuitPython Performance Analysis

## Scope

Only analyse and modify files under `pmpge/`. Do not modify test files, validate scripts, examples, or drivers unless explicitly asked.

## Priority Order

1. **Speed** — reduce CPU cycles in hot paths (update/draw loops called 30–60 times per second)
2. **Memory allocation** — minimise heap allocations inside loops to reduce GC pressure
3. **Memory footprint** — reduce overall RAM usage to stay within microcontroller limits (~140–165 KB total heap on target devices)
4. **Readability** — do not produce code so dense it cannot be understood; always add a comment when a non-obvious optimisation is applied

## Procedure

### Step 1 — Identify hot paths

Read the target file(s). Identify code called repeatedly in the game loop:
- `update()` / `update_hierarchy()` and everything they call
- `draw()` / `draw_hierarchy()` and everything they call
- Handler dispatch loops (iterating `update_handlers`, `draw_handlers`, etc.)
- Any function called per-child in a hierarchy traversal

Cold paths (setup, init, destroy) are low priority.

### Step 2 — Run the analysis checklist

Apply every rule in [analysis-checklist.md](./references/analysis-checklist.md) to the code under review.

### Step 3 — Consult optimisation techniques

For each identified issue, use [circuitpython-optimisations.md](./references/circuitpython-optimisations.md) to select the correct fix.

### Step 4 — Apply changes

- Make the minimum change that achieves the optimisation.
- Add a short inline comment starting with `# PERF:` on any line where the code was intentionally made less readable for performance reasons. Example:
  ```python
  _upd = self._update_handlers  # PERF: cache attribute lookup out of loop
  ```
- Do not add `# PERF:` comments to changes that are equally readable (e.g. switching a `for` loop to a list comprehension for a simple case).
- Do not refactor, rename, or restructure beyond what the optimisation requires.

### Step 5 — Report findings

After applying changes, produce a short summary in this format:

```
## Performance Analysis: <filename>

### Hot paths identified
- <list>

### Changes made
| Location | Issue | Change | Expected benefit |
|----------|-------|--------|-----------------|
| ...      | ...   | ...    | ...             |

### Not changed (with reason)
- <anything you considered but decided was not worth the readability trade-off>
```
