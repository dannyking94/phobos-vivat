# Local patches applied to Phobos

This file tracks manual edits made to the upstream Phobos source. If you
re-clone or update Phobos, re-apply these.

## 1. Blender 4.1+/5.x operator `__init__` compatibility

**File:** `phobos/blender/operators/editing.py`
**Class:** `DefineJointConstraintsOperator` (around line 1632)
**Date applied:** 2026-05-26
**Blender version:** 5.1.2
**Phobos version:** master (post-2.1.0)

### Symptom

Clicking "Define Joint" in the Phobos sidebar raised:

```
Python: TypeError: DefineJointConstraintsOperator.__init__() takes 1
positional argument but 2 were given
```

### Cause

Blender 4.1+ changed the operator API: `bpy.types.Operator.__init__` now
receives a `context` argument. Phobos's operator defined `__init__(self)`
with no extra args, so the new positional arg from Blender raises TypeError.

### Fix

Change:

```python
def __init__(self):
    self.sRefBody = False
    ...
```

to:

```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.sRefBody = False
    ...
```

`*args, **kwargs` accepts whatever Blender passes; `super().__init__` keeps
the base `Operator` initialisation correct.

### Re-applying after a Phobos update

```bash
grep -n "def __init__(self):" ~/Apps/blender/phobos/phobos/blender/operators/editing.py
```

If that returns a hit on the `DefineJointConstraintsOperator` class, apply
the same edit. Also worth grepping the whole operators directory in case
upstream adds more no-arg `__init__` methods:

```bash
grep -rn "def __init__(self):" ~/Apps/blender/phobos/phobos/blender/operators/
```

### Where the live copy lives

Blender loads the add-on from its own addons folder, not from
`~/Apps/blender/phobos/`. The patched file in this source tree only takes
effect after re-zipping and reinstalling:

```bash
cd ~/Apps/blender/phobos
rm -f /tmp/phobos.zip
zip -r /tmp/phobos.zip phobos > /dev/null
# Then in Blender: Edit -> Preferences -> Add-ons -> remove Phobos,
# install from /tmp/phobos.zip, enable, restart.
```

Alternatively, edit the installed copy directly:

```
~/.config/blender/5.1/scripts/addons/phobos/blender/operators/editing.py
```

and restart Blender.

### Upstream

Worth reporting at https://github.com/dfki-ric/phobos/issues — README still
says "tested with Blender 3.3 LTS" and master only has partial 4.0/5.0
compat fixes.
