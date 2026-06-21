# CircuitPython Performance Analysis Checklist

Apply each item below to the code under review. Mark as applicable (A), not applicable (N/A), or already optimised (OK).

---

## Speed Checklist

### S1 — Attribute lookup in loops
**Issue:** `self.foo` inside a loop causes a dictionary lookup on every iteration.  
**Check:** Is any `self.x` attribute accessed more than once inside a `for`/`while` loop body or in a function called per-frame?  
**Fix:** Cache to a local variable before the loop.
```python
# Before
for h in self._update_handlers:
    h(dt)
    if self._active:   # repeated lookup

# After
handlers = self._update_handlers  # PERF: cache attribute lookup
active = self._active              # PERF: cache attribute lookup
for h in handlers:
    h(dt)
    if active:
```

---

### S2 — Global variable access in hot paths
**Issue:** Global variable lookup is slower than local variable lookup in CPython; same in CircuitPython.  
**Check:** Does a hot-path function read a module-level global repeatedly?  
**Fix:** Assign to a local at the top of the function.

---

### S3 — Repeated method calls that return the same value
**Issue:** `len(self._children)` called multiple times per loop iteration recomputes each time.  
**Check:** Is the same method called with the same arguments more than once inside a loop?  
**Fix:** Call once and store in a local.

---

### S4 — `isinstance` / `hasattr` in hot paths
**Issue:** Both are relatively expensive. `hasattr` allocates on every call.  
**Check:** Is `isinstance` or `hasattr` called inside an update/draw loop?  
**Fix:**
- For `isinstance`: use a boolean flag set at construction time.
- For `hasattr`: use `getattr(obj, 'attr', None) is not None` or pre-check at init.

---

### S5 — String formatting in hot paths
**Issue:** f-strings and `str.format()` always allocate a new string object.  
**Check:** Is any string formatted inside a loop or per-frame function?  
**Fix:** Move to cold path (e.g. only format when a debug flag is True and only outside the loop), or pre-build the string.

---

### S6 — List/tuple building in hot paths
**Issue:** `[a, b, c]` and `(a, b, c)` allocate a new object every call.  
**Check:** Is a list or tuple created inside a hot-path function solely to pass to another function?  
**Fix:** Use positional arguments, or pre-allocate a buffer and mutate it in-place (e.g. a `bytearray` or a fixed-length list).

---

### S7 — `for` loop vs built-in iteration
**Issue:** Hand-rolled accumulation loops are slower than `sum()`, `any()`, `all()`, `map()`.  
**Check:** Is there a loop that simply accumulates a value that a built-in could compute?  
**Fix:** Replace with the appropriate built-in.

---

### S8 — Short-circuit evaluation
**Issue:** Unnecessary work done when an early exit condition is available.  
**Check:** Does a condition check cheap things after expensive things?  
**Fix:** Reorder so the cheapest / most-likely-to-fail check is first.

---

### S9 — Integer vs float arithmetic
**Issue:** Float arithmetic is slower on microcontrollers with no FPU (e.g. ATSAMD51). Integer arithmetic avoids this.  
**Check:** Is position/velocity/time stored as `float`? Could it be stored as an integer in a smaller unit (e.g. thousandths of a pixel)?  
**Fix:** Document any such conversion clearly — this is a significant API change so propose but do not apply without confirmation.

---

### S10 — `__slots__`
**Issue:** Without `__slots__`, each instance carries a `__dict__`, adding a dict allocation and slowing attribute access.  
**Check:** Does the class lack `__slots__`? Is it instantiated many times?  
**Fix:** Add `__slots__` listing all instance attributes. Note: subclasses must also define `__slots__` for the benefit to carry through. Requires careful review of the full class hierarchy.

---

## Memory Allocation Checklist

### M1 — Temporary objects inside loops
**Issue:** Any allocation inside a loop runs the GC more frequently, causing stutters.  
**Check:** Is any object (list, tuple, string, dict) created inside a loop that could be created once outside?  
**Fix:** Hoist the allocation out of the loop. If the object must vary, consider a pre-allocated mutable buffer.

---

### M2 — Closure allocation
**Issue:** Lambda and inner functions allocated inside a loop create a new function object on each iteration.  
**Check:** Is a `lambda` or nested `def` inside a loop?  
**Fix:** Lift to a module-level or class-level function and pass needed state as arguments.

---

### M3 — Generator vs list comprehension
**Issue:** A list comprehension builds a full list in memory. A generator expression produces values one at a time.  
**Check:** Is a list comprehension used only for iteration (e.g. `for x in [f(y) for y in items]`)?  
**Fix:** Replace with a generator expression: `for x in (f(y) for y in items)`.  
**Counter-check:** If the result is iterated more than once, a list is correct — generators are single-use.

---

### M4 — `gc.collect()` at safepoints
**Issue:** The GC can run at any time, causing unpredictable pauses. Calling `gc.collect()` at known low-activity moments (after loading a scene, after destroying objects) gives you control.  
**Check:** Is there a natural safepoint (scene load/unload, after `destroy()`) where `gc.collect()` is not called?  
**Fix:** Add `gc.collect()` at that point. Import `gc` if not already imported.

---

### M5 — Wildcard imports
**Issue:** `from module import *` imports every public name, bloating the module namespace.  
**Check:** Is `from x import *` used anywhere in `pmpge/`?  
**Fix:** Replace with explicit imports of only what is needed.

---

### M6 — Pre-allocation of buffers
**Issue:** Creating a new `bytearray`, `list`, or `array` inside a frequently called function re-allocates every call.  
**Check:** Is a buffer created inside a function that is called per-frame?  
**Fix:** Create the buffer once as a class or module attribute and pass/reuse it.

---

## Readability Rules

### R1 — Comment all PERF changes
Every line changed for a non-obvious performance reason must have a `# PERF: <reason>` comment.

### R2 — Preserve public API
Do not rename public methods, change function signatures, or alter class names as part of a performance optimisation. If an API change is needed, flag it as a proposal.

### R3 — One change at a time per location
Do not combine multiple optimisations in one edit unless they are inseparable. Make each change reviewable in isolation.

### R4 — Complexity limit
If an optimisation would make the code significantly harder to reason about (e.g. bitmask tricks, unrolled loops, obscure slice operations), prefer a clear comment explaining what it does over the raw optimisation. If the gain is marginal, skip it.
