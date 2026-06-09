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

## 4. Blender 5.x Principled BSDF input names (b41Export gate)

**File:** `phobos/blender/io/blender2phobos.py`
**Function:** `deriveMaterial` (line 70)
**Date applied:** 2026-05-26
**Blender version:** 5.1.2
**Phobos version:** master (post-2.1.0)

### Symptom

Exporting a model (Phobos sidebar → Export) raised:

```
KeyError: 'bpy_prop_collection[key]: key "Specular" not found'
```

from `deriveMaterial`, while trying to read
`Principled BSDF.inputs["Specular"].default_value`.

### Cause

The `b41Export` flag was defined as:

```python
b41Export = bpy.app.version[0] == 4 and bpy.app.version[1] >= 1
```

This is true only for Blender 4.1–4.x. On Blender 5.x it falls into the
`else` branch, which references the pre-4.1 input names `"Specular"` and
`"Emission"`. Those were renamed to `"Specular IOR Level"` and
`"Emission Color"` in Blender 4.1 and the old names no longer exist in 5.x,
so the lookup raises `KeyError`.

### Fix

Change the comparison to a tuple comparison so 5.x (and later) is also
treated as "post-4.1":

```python
b41Export = bpy.app.version >= (4, 1)
```

`bpy.app.version` is a `(major, minor, patch)` tuple, so this evaluates to
`True` for 4.1, 4.2, …, 5.0, 5.1, etc.

### Re-applying after a Phobos update

```bash
grep -n "b41Export = bpy.app.version\[0\] == 4" ~/Apps/blender/phobos/phobos/blender/io/blender2phobos.py
```

If that returns a hit, replace with the tuple comparison. Same edit needs
to be made in the installed copy at
`~/.config/blender/5.1/scripts/addons/phobos/blender/io/blender2phobos.py`.

### Upstream

Same tracker as patches #1–#3. Worth filing as a single "Blender 5.x
compatibility" issue with all four patches.

## 5. Create Collision Object(s) shows no dialog

**File:** `phobos/blender/operators/editing.py`
**Class:** `CreateCollisionObjects` (around line 1276)
**Date applied:** 2026-05-26
**Blender version:** 5.1.2 (UX issue, version-independent)
**Phobos version:** master (post-2.1.0)

### Symptom

Clicking "Create Collision Object(s)" in the Phobos sidebar runs the
operator immediately with the default `Collision Type = box` and never
asks the user. The only ways to change the type were:

1. Press F9 right after the operator runs (Blender's "Adjust Last
   Operation" panel), or
2. Call the operator from the Python console with
   `bpy.ops.phobos.create_collision_objects(property_colltype='cylinder')`.

Neither is discoverable, and a wheel collision created as a box is wrong
for almost any AMR/robot.

### Cause

`CreateCollisionObjects` defined `execute` but no `invoke`. Without
`invoke`, Blender calls `execute` directly at the property defaults and
never displays a dialog. Other Phobos operators (e.g. `SetGeometryType`,
`GenerateInertialObjectsOperator`) do define `invoke` and call
`invoke_props_dialog`, so they pop up correctly.

### Fix

Add a minimal `invoke` method that opens a props dialog:

```python
def invoke(self, context, event):
    return context.window_manager.invoke_props_dialog(self, width=300)
```

Place it just above `execute`. The existing `property_colltype` EnumProperty
is automatically rendered in the dialog because the operator has no
custom `draw` method — Blender falls back to drawing all annotated
properties.

### Re-applying after a Phobos update

```bash
grep -n "class CreateCollisionObjects" ~/Apps/blender/phobos/phobos/blender/operators/editing.py
```

Then inspect the class — if there's no `invoke` method, add the snippet
above. Same edit needs to be made in the installed copy at
`~/.config/blender/5.1/scripts/addons/phobos/blender/operators/editing.py`.

### Upstream

This is a pure UX fix, not version-specific. Worth a small standalone PR
to dfki-ric/phobos.

## 6. Inertial creation: `fuse_inertia_data` returns COM as a list

**File:** `phobos/blender/model/inertia.py`
**Function:** `fuse_inertia_data` (line 134, the no-inertials early return)
**Date applied:** 2026-06-08
**Blender version:** 5.1.2
**Phobos version:** master (post-2.1.0)

### Symptom

Selecting (or having active) a link object that has no inertial child with
inertia data — e.g. a freshly duplicated link/visual — makes the Phobos
sidebar crash on every redraw:

```
File ".../blender/io/blender2phobos.py", line 418, in deriveLink
    com.x = com.x*obj.scale[0]
AttributeError: 'list' object has no attribute 'x'
```

### Cause

`deriveLink` calls `fuse_inertia_data` and then does `com.x`, expecting a
`mathutils.Vector`. The normal path returns a `Vector` (from
`combine_com_3x3`), but the early return when there are no inertials to fuse
returned a plain Python list:

```python
if not inertials:
    return 1e-3, [0.0, 0.0, 0.0], numpy.diag([1e-3, 1e-3, 1e-3])
```

A list has no `.x`, so the GUI draw throws.

### Fix

Return a `mathutils.Vector` so the type matches the success path
(`mathutils` is already imported in the file):

```python
if not inertials:
    return 1e-3, mathutils.Vector((0.0, 0.0, 0.0)), numpy.diag([1e-3, 1e-3, 1e-3])
```

### Re-applying after a Phobos update

```bash
grep -n "return 1e-3, \[0.0, 0.0, 0.0\], numpy.diag" ~/Apps/blender/phobos/phobos/blender/model/inertia.py
```

If that returns a hit, swap the list for `mathutils.Vector((0.0, 0.0, 0.0))`.
Same edit in the installed copy at
`~/.config/blender/5.1/scripts/addons/phobos/blender/model/inertia.py`.

### Upstream

Same tracker as patches #1–#5.

## 7. Inertial creation: `validateInertiaData` calls `.phobostype` on a dict

**File:** `phobos/blender/utils/validation.py`
**Function:** `validateInertiaData` (line 596)
**Date applied:** 2026-06-08
**Blender version:** 5.1.2
**Phobos version:** master (post-2.1.0)

### Symptom

Running "Create Inertial" (which passes a freshly built inertia dictionary)
raised:

```
File ".../blender/utils/validation.py", line 596, in validateInertiaData
    if obj.phobostype != 'inertial':
AttributeError: 'dict' object has no attribute 'phobostype'
```

### Cause

`validateInertiaData` is documented to accept *either* a dict or a Blender
object, and branches on `isinstance(obj, dict)` further down. But the
phobostype check at the top ran unconditionally, before that branch, so a
dict input crashes immediately:

```python
if obj.phobostype != 'inertial':
    ...
```

### Fix

Guard the object-only check so dicts skip it and fall through to the
existing dict-validation path:

```python
if not isinstance(obj, dict) and obj.phobostype != 'inertial':
    ...
```

### Re-applying after a Phobos update

```bash
grep -n "if obj.phobostype != 'inertial':" ~/Apps/blender/phobos/phobos/blender/utils/validation.py
```

If that returns a hit inside `validateInertiaData`, prepend
`not isinstance(obj, dict) and`. Same edit in the installed copy at
`~/.config/blender/5.1/scripts/addons/phobos/blender/utils/validation.py`.

### Upstream

Same tracker as patches #1–#5.

## 8. Inertial creation: `selectObjects` `mode_set` with no usable active object

**File:** `phobos/blender/utils/selection.py`
**Function:** `selectObjects` (line 318)
**Date applied:** 2026-06-08
**Blender version:** 5.1.2
**Phobos version:** master (post-2.1.0)

### Symptom

Finishing "Create Inertial" raised:

```
File ".../blender/utils/selection.py", line 319, in selectObjects
    bpy.ops.object.mode_set(mode='OBJECT')
RuntimeError: Operator bpy.ops.object.mode_set.poll() Context missing active object
```

### Cause

`createInertial` makes the inertial box in the `inertial` collection, then
calls `selectObjects`, which tries to force Object Mode. The guard only
checked `view_layer.objects.active` — a reference that can be stale or point
to an object not present in the active context (e.g. an excluded/hidden
collection) — while `mode_set.poll()` checks `context.active_object`, which
is `None`. So the guard passes but the operator's poll fails.

### Fix

Also require `context.active_object`, and swallow the `RuntimeError`
defensively (the same function already try/excepts `select_set` a few lines
below for an analogous reason):

```python
if bpy.context.view_layer.objects.active and bpy.context.active_object:
    try:
        bpy.ops.object.mode_set(mode='OBJECT')
    except RuntimeError:  # active object not in current context (e.g. excluded collection)
        pass
```

### Re-applying after a Phobos update

```bash
grep -n "if bpy.context.view_layer.objects.active:" ~/Apps/blender/phobos/phobos/blender/utils/selection.py
```

If that returns a hit in `selectObjects`, apply the guard + try/except above.
Same edit in the installed copy at
`~/.config/blender/5.1/scripts/addons/phobos/blender/utils/selection.py`.

### Upstream

Same tracker as patches #1–#5. Patches #6–#8 are all on the inertial-creation
path and were hit in sequence while adding an inertial to a duplicated link.

## 9. Collision fitter ignores object scale for primitive-type visuals

**File:** `phobos/blender/operators/editing.py`
**Class:** `CreateCollisionObjects.execute` (lines 1341, 1348, 1355)
**Date applied:** 2026-06-08
**Blender version:** 5.1.2
**Phobos version:** master (post-2.1.0)

### Symptom

"Create Collision Object(s)" with type box/cylinder/sphere produces a
correct collision when the source **visual is a mesh** (`geometry/type=mesh`),
but a **wrongly-scaled and wrongly-oriented** collision when the visual is a
**primitive** (`geometry/type=cylinder|box|sphere`). E.g. fitting a cylinder
to a scaled cylinder-primitive wheel visual yields a radius-1 / length-2
collision rotated 90° about Y, instead of the visual's actual size with no
rotation.

### Cause

The operator passes the *geometry's* scale to the fitter:

```python
geometry, transform = geo.create_cylinder(vis, scale=getattr(phobos_vis.geometry, "scale", 1))
```

`deriveVisual` returns a `Mesh` geometry (which carries `.scale` = the object
scale) for mesh visuals, but a `Cylinder`/`Box`/`Sphere` geometry (which
encodes size as radius/length and has **no `.scale` attribute**) for primitive
visuals. So `getattr(..., "scale", 1)` falls back to **1** for primitives, and
`create_cylinder` builds from the raw **unit** mesh `bound_box` (2,2,2):

- wrong scale — unit size instead of the scaled size, and
- wrong orientation — a unit cylinder's bbox is a perfect cube, so the axis
  heuristic `argmax(|extent - mean|)` is all-zeros → `np.argmax` returns 0 →
  X is picked as the long axis and `rpy=[0, pi/2, 0]` is applied.

Mesh visuals have non-uniform `.scale`, so the Z axis stands out and no
rotation is applied — which is why mesh visuals worked.

### Fix

Pass the object's own scale (correct for both mesh and primitive visuals) in
all three primitive branches:

```python
geometry, transform = geo.create_box(vis, scale=list(vis.scale), oriented=False)
geometry, transform = geo.create_cylinder(vis, scale=list(vis.scale),)
geometry, transform = geo.create_sphere(vis, scale=list(vis.scale),)
```

Verified headless: for a scaled cylinder-primitive visual this yields
`radius=0.2197 length=0.2165` with an identity transform, identical to the
working mesh-visual path.

### Re-applying after a Phobos update

```bash
grep -n 'getattr(phobos_vis.geometry, "scale", 1)' ~/Apps/blender/phobos/phobos/blender/operators/editing.py
```

If that returns hits in `CreateCollisionObjects.execute`, replace each with
`list(vis.scale)`. Same edit in the installed copy at
`~/.config/blender/5.1/scripts/addons/phobos/blender/operators/editing.py`.

### Upstream

Same tracker as patches #1–#5. A more thorough upstream fix would also make
the cube-bbox axis heuristic in `geometry.create_cylinder` deterministic
(fall back to Z, or skip rotation, when extents are equal).
