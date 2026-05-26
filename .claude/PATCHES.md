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

## 2. Blender 5.x `_bpy_types.Mesh` whitelist

**File:** `phobos/io/representation.py`
**Line:** 40 (where `MESH_DATA_TYPES` is extended for Blender)
**Date applied:** 2026-05-26
**Blender version:** 5.1.2
**Phobos version:** master (post-2.1.0)

### Symptom

Selecting any visual object whose geometry type is `mesh` triggers the
Phobos sidebar to derive a representation, which fails with:

```
AssertionError: The input type _bpy_types.Mesh of object Cylinder is not
recognized.
```

### Cause

Phobos derives the input type with
`str(type(mesh))[8:-2]` (e.g. `<class '_bpy_types.Mesh'>` → `_bpy_types.Mesh`)
and then checks it against the `MESH_DATA_TYPES` whitelist. In Blender 5.x
the module is `_bpy_types` (leading underscore), but the whitelist only
contains `bpy_types.Mesh`, so the assertion fires.

### Fix

Change:

```python
MESH_DATA_TYPES += ["bpy_types.Mesh"]
```

to:

```python
MESH_DATA_TYPES += ["bpy_types.Mesh", "_bpy_types.Mesh"]
```

Keeping both entries preserves compatibility with older Blender versions
that still expose the type as `bpy_types.Mesh`.

### Re-applying after a Phobos update

```bash
grep -n 'MESH_DATA_TYPES += \["bpy_types.Mesh"\]$' ~/Apps/blender/phobos/phobos/io/representation.py
```

If that returns a hit, add the `"_bpy_types.Mesh"` entry. Same edit needs
to be made in the installed copy at
`~/.config/blender/5.1/scripts/addons/phobos/io/representation.py` (or re-zip
and reinstall — see patch #1).

### Upstream

Same tracker as patch #1. A more robust upstream fix would be to use
`isinstance(mesh, bpy.types.Mesh)` instead of the string-based whitelist.

## 3. Blender 5.x removed `Bone.select`

**File:** `phobos/blender/model/joints.py`
**Function:** `setJointConstraints` (around line 208-210)
**Date applied:** 2026-05-26
**Blender version:** 5.1.2
**Phobos version:** master (post-2.1.0)

### Symptom

Clicking "Define Joint" (after picking a joint type) raised:

```
AttributeError: 'Bone' object has no attribute 'select'
```

and then a cascading error in the sidebar:

```
KeyError: 'joint/type: The joint type of steer1 has not been properly defined.'
```

The second error happens because the first one aborted `setJointConstraints`
before the `joint/type` custom property got written.

### Cause

Blender 5.x removed the `select` attribute from `bpy.types.Bone` (the
armature-data bone). Selection state now lives on pose bones or is managed
through the active object. Phobos's `setJointConstraints` did:

```python
joint.data.bones.active = joint.pose.bones[0].bone
joint.data.bones.active.select = True   # <-- AttributeError on 5.x
```

### Fix

Setting `joint.data.bones.active = ...` is enough — the subsequent
constraint operators use the active bone, not the selection. Wrap the
`.select = True` line in a try/except so it's a no-op on Blender 5.x while
still working on older versions:

```python
joint.data.bones.active = joint.pose.bones[0].bone
try:
    joint.data.bones.active.select = True
except AttributeError:
    pass
remove_screwdrivers(joint)
```

### Re-applying after a Phobos update

```bash
grep -n "joint.data.bones.active.select = True" ~/Apps/blender/phobos/phobos/blender/model/joints.py
```

If that returns a hit, wrap the line in `try/except AttributeError`. Same
edit needs to be made in the installed copy at
`~/.config/blender/5.1/scripts/addons/phobos/blender/model/joints.py`.

### Upstream

Same tracker as patches #1 and #2.
