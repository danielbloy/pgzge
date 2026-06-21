# CircuitPython Optimisation Techniques

Detailed guidance on optimisation techniques applicable to this codebase. Each technique includes when to apply it, how to apply it, and the expected trade-offs.

---

## 1. Cache Attribute Lookups

**When:** Any attribute accessed more than once in a loop body or called more than ~5 times per frame.

**How:**
```python
# Before — two dictionary lookups per iteration
for handler in self._update_handlers:
    if self._active:
        handler(dt)

# After
_handlers = self._update_handlers  # PERF: cache attribute lookup out of loop
_active = self._active              # PERF: cache attribute lookup out of loop
for handler in _handlers:
    if _active:
        handler(dt)
```

**Expected benefit:** 10–30% speedup in tight loops on CircuitPython (no hardware dict cache).

**Trade-off:** Local shadows the live attribute — if the attribute is mutated during the loop, the cached value is stale. Only safe when the attribute is not mutated inside the loop.

---

## 2. Use `__slots__`

**When:** A class is instantiated many times (e.g. `GameObject`) and does not need a dynamic `__dict__`.

**How:**
```python
class GameObject:
    __slots__ = ('_parent', '_children', '_active', '_alive', '_enabled', '_visible',
                 '_name', 'update_handlers', 'draw_handlers', ...)

    def __init__(self, ...):
        self._parent = None
        ...
```

**Expected benefit:** Reduces per-instance memory by ~200–400 bytes (eliminates `__dict__`). Also speeds up attribute access.

**Trade-off:** Significant — every subclass must also define `__slots__` (or all benefit is lost). Breaks `__dict__`-based patterns (e.g. dynamic attribute setting, `vars(obj)`). Requires a full audit of the class hierarchy. **Propose, don't apply without confirmation.**

**Note for this codebase:** `Sprite` inherits from `GameObject`; traits copy attributes dynamically. Verify that dynamic attribute assignment via traits is compatible before adding `__slots__`.

---

## 3. Integer Arithmetic Instead of Float

**When:** Position, velocity, or time values are stored as floats but only need integer precision. Particularly useful on ATSAMD51 (Edge Badge, Feather M4) which has a hardware FPU but integer operations are still faster for simple maths.

**How:**
```python
# Before — float pixels per second
self._velocity_x: float = 0.0  # pixels/second

# After — integer thousandths of a pixel per second
self._velocity_x: int = 0  # PERF: thousandths of a pixel/second to avoid float arithmetic
# Convert only at the draw boundary:
draw_x = self._x // 1000
```

**Expected benefit:** Up to 2x speedup on boards without FPU. Smaller benefit on boards with FPU.

**Trade-off:** Significant API change. Requires updating all callers. **Propose, don't apply without confirmation.**

---

## 4. Avoid Allocation in Hot Paths

**When:** Any object (list, tuple, string, dict, lambda) is created inside `update()`, `draw()`, or their hierarchy traversal loops.

**Pattern — pre-allocate a reusable buffer:**
```python
class Renderer:
    def __init__(self):
        self._rect_buffer = [0, 0, 0, 0]  # PERF: pre-allocated to avoid per-frame alloc

    def draw_rect(self, x, y, w, h):
        buf = self._rect_buffer
        buf[0] = x
        buf[1] = y
        buf[2] = w
        buf[3] = h
        self._backend.blit(buf)
```

**Pattern — avoid temporary tuples:**
```python
# Before — creates a new tuple every call
self._backend.draw(sprite, (x, y))

# After — use positional arguments if the API allows
self._backend.draw(sprite, x, y)
```

---

## 5. Use `gc.collect()` at Safepoints

**When:** After loading/unloading a scene, after `destroy()` calls that remove large subtrees, or at any point where a brief pause is acceptable.

**How:**
```python
import gc

def load_scene(self, scene):
    if self._current_scene:
        self._current_scene.destroy()
        gc.collect()  # PERF: collect immediately after large deallocation to avoid mid-frame GC
    self._current_scene = scene
    scene.setup(self)
```

**Expected benefit:** Reduces the chance of mid-frame GC pauses that cause visible frame drops.

**Trade-off:** Adds a brief pause at scene transitions. Acceptable for transitions but not inside the game loop.

---

## 6. Replace `hasattr` with a Sentinel or Flag

**When:** `hasattr(obj, 'method')` is called per-frame or per-object in a loop.

**How:**
```python
# Before
for child in self._children:
    if hasattr(child, 'update'):
        child.update(dt)

# After — use a flag set at construction time
for child in self._children:
    if child._has_update:  # PERF: boolean flag replaces hasattr() call
        child.update(dt)
```

**Alternatively** — use duck typing: always define the method on the base class as a no-op, then the `if` check is unnecessary:
```python
class GameObject:
    def update(self, dt: float) -> None:
        pass  # default no-op; overridden in subclasses
```

---

## 7. Use Built-in Functions

**When:** A loop simply aggregates a sequence in a way a built-in can handle.

| Pattern | Replace with |
|---------|-------------|
| `result = []; for x in items: result.append(f(x))` | `result = [f(x) for x in items]` |
| `total = 0; for x in items: total += x` | `total = sum(items)` |
| `found = False; for x in items: if cond(x): found = True; break` | `found = any(cond(x) for x in items)` |
| `all good; for x in items: if not cond(x): all_good = False; break` | `all_good = all(cond(x) for x in items)` |

---

## 8. Lift Invariants Out of Loops

**When:** A condition or expression inside a loop does not depend on the loop variable.

```python
# Before
for child in self._children:
    if self._active and self._visible:  # invariant check repeated each iteration
        child.draw(surface)

# After
if self._active and self._visible:  # PERF: invariant check lifted outside loop
    for child in self._children:
        child.draw(surface)
```

---

## 9. Avoid Wildcard Imports

**When:** `from module import *` is used anywhere in `pmpge/`.

**How:** Replace with explicit imports:
```python
# Before
from pmpge.palette import *

# After
from pmpge.palette import BLACK, WHITE, RED  # only what is needed
```

**Expected benefit:** Reduces namespace pollution, slightly reduces module load time and memory.

---

## 10. Generator Expressions for Single-Use Iteration

**When:** A list comprehension is constructed purely to iterate over it once.

```python
# Before — builds a full list
total = sum([child.cost() for child in self._children])

# After — generator avoids the intermediate list
total = sum(child.cost() for child in self._children)  # PERF: generator avoids list alloc
```

**Counter-check:** If the sequence is iterated more than once, a list is correct.

---

## 11. Compile to `.mpy`

**When:** Deploying to a device. `.mpy` files are pre-compiled bytecode and load faster, use less RAM, and execute slightly faster than `.py` files.

**How:** Use `mpy-cross` from the CircuitPython tools:
```sh
mpy-cross pmpge/game_object.py
```

This produces `game_object.mpy` which CircuitPython prefers over the `.py` file.

**Note:** This is a deployment step, not a code change. Do not commit `.mpy` files to version control unless intentional.

---

## 12. Reduce `update_handlers` / `draw_handlers` Dispatch Overhead

**When:** The handler lists are iterated every frame for every `GameObject`, and most objects have zero or one handler.

**Pattern — fast-path for empty list:**
```python
def update_hierarchy(self, dt: float) -> None:
    _handlers = self._update_handlers
    if _handlers:  # PERF: skip loop entirely when no handlers registered
        for handler in _handlers:
            handler(dt)
    _children = self._children
    if _children:  # PERF: skip loop entirely when no children
        for child in _children:
            if child._active:
                child.update_hierarchy(dt)
```

**Expected benefit:** Removes two loop setups per frame per object when lists are empty, which is the common case for leaf nodes.

---

## Device Memory Constraints (Reference)

| Device | Total heap | Notes |
|--------|-----------|-------|
| Adafruit Edge Badge (ATSAMD51) | ~146 KB | Rich board; measured ~126 KB peak used |
| Pico System (RP2040) | ~165 KB | Rich board; measured ~164 KB peak used |
| Raspberry Pi Pico (RP2040) | ~192 KB | Plain board |
| Raspberry Pi Pico 2 (RP2350) | ~512 KB | Plain board |

Target: keep peak RAM usage below 80% of total heap to leave headroom for user code.
