# CircuitPython optimization checklist

Concrete rules to check for, grounded in this codebase. Treat
`validate/performance/README.md`'s "Optimisation roadmap" as the canonical,
evolving list — this file adds detail/examples underneath those items and a
few extras that aren't there yet. If the two ever disagree, the roadmap file
wins; update this file or flag the conflict to the user.

## Speed (check these first)

- **Float accumulation in hot-path `update()`**. `pmpge/traits/physics.py`
  (`Velocity`, `Acceleration`, `Friction`, `AngularMotion`) accumulates
  `float` position/velocity every frame via `dt * vx`. CircuitPython has no
  hardware FPU on most reference boards (SAMD51, RP2040), so float math is
  emulated in software and meaningfully slower than int math. The roadmap's
  fix is converting units to thousandths-of-a-pixel-per-second ints. When you
  touch these files, check whether the conversion is consistent across *all*
  traits that share state (e.g. `Velocity.vx` feeding `BoundVelocity`,
  `Acceleration`, `Friction`, `HorizontalBounce`/`VerticalBounce` all assume
  the same units) — a partial conversion is worse than none.
- **Repeated attribute/module lookups inside a per-frame loop.** Good
  precedent already in the codebase: `HorizontalBounce.update`,
  `VerticalBounce.update`, `HorizontalOscillator.update` all cache
  `self.x`/`self.vx` into locals once at the top. `AngularMotion.update` does
  not cache the `math` module lookup (`math.cos`, `math.sin` resolve `math`
  as a global on every call) — worth a local alias or `from math import
  sin, cos` at module scope. Apply the same "cache into locals at the top of
  `update()`" pattern anywhere it's missing in a hot-path method.
- **Unnecessary per-frame allocation in hierarchy traversal.**
  `update_hierarchy()` in `pmpge/game_object.py` rebuilds two full list
  comprehensions (`go._children` filtered twice) for *every* GameObject that
  has children, on *every* update where `GameObject.something_destroyed` is
  True — even if that particular GameObject's children are all still alive.
  A per-object "did any of my direct children die" check (or tracking dead
  children incrementally at `destroy()` time) would avoid the reallocation
  for the common case where only one branch of the tree changed. Any fix here
  must preserve the existing traversal order contract (see the big comment
  block above `update_hierarchy`) and the `something_destroyed` reset
  semantics.
- **Recursion depth in hierarchy code.** Note `update_hierarchy`,
  `draw_hierarchy`, and `traverse_hierarchy` are already implemented
  iteratively with a level-by-level swap (`current, children = children,
  current`) specifically to avoid recursion overhead — this is already
  optimized. Don't "simplify" it back to recursive calls; that would be a
  regression, not a cleanup.
- **Reflection in the hot path vs. cold path.** `apply_trait()` uses `dir()` +
  `getattr`/`setattr` reflection, which is slow — but it only runs once per
  trait application at GameObject construction time, not per-frame. Don't
  spend effort optimizing it unless profiling shows construction-time cost
  actually matters (e.g. a game that recreates many GameObjects per second,
  which the target performance envelope — 20-50 GameObjects total — suggests
  is not the common case).
- **Method/handler-list indirection.** `draw_handlers`/`update_handlers` add a
  function-call layer per trait per frame. This is inherent to the
  traits-without-subclassing design goal in CLAUDE.md ("avoid students
  needing to write the same boilerplate") — do not propose collapsing it
  away; that would undermine the actual design goal for a speed gain the
  target hardware doesn't need.
- **Display I/O batching.** Per the roadmap: prefer `auto_refresh = False`
  with an explicit `refresh()` call, and check graphics drivers under
  `pmpge/drivers/graphics/` for redundant per-object display writes that
  could be batched into one write per frame.
- **`gc.collect()` at safepoints.** Check for natural points to call this
  (scene/level transitions, `execute()`'s teardown already does this) rather
  than relying on it happening implicitly under GC pressure mid-frame.

## Memory (check second)

- **Prefer tuples over lists for fixed-size immutable state.** Existing good
  precedent: `bounds_velocity`, `limits_x`, `limits_y` in
  `pmpge/traits/physics.py` are already tuples, not lists — use this as the
  template when reviewing new trait state.
- **`__slots__` is a bigger discussion, not a drop-in fix.** `GameObject`
  instances gain arbitrary attributes at runtime via `apply_trait()`'s
  `setattr(self, attribute, getattr(trait, attribute))` loop. Adding
  `__slots__` to `GameObject` or trait classes would require pre-declaring
  every attribute any trait might ever set, which conflicts with the
  "traits without subclassing" design. Flag this as a design question for the
  user rather than applying it unilaterally.
- **Don't grow unbounded lists.** `remove_child`/the hierarchy traversal's
  child-pruning already keep `_children` bounded to alive objects — check any
  new code (e.g. object pools, event queues) follows the same discipline
  rather than appending without ever trimming.
- **Avoid new object churn in per-frame code.** Every tuple/list/dict
  constructed inside `update()`/`draw()` is GC pressure on a device with a
  few hundred KB of RAM. Look for per-frame construction of temporary
  containers that could instead be precomputed once in `__init__` (e.g.
  `RateLimiter.__init__` precomputing `_call_delta = 1 / rate` once instead
  of dividing every call is the existing template to follow).

## References

- `validate/performance/README.md` — canonical, evolving optimisation
  roadmap and results log.
- `devices/README.md` — target performance envelope and reference hardware.
- `validate/validation.md` — how to actually run validation on real hardware.
