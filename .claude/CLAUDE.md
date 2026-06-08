# Project notes for Claude

This repo is the **Phobos** Blender add-on (robot model editor: URDF/SDF ↔ Blender).
See `.claude/PATCHES.md` for local Blender-5.x compatibility patches applied to the source.

## Running Blender headless (for inspecting / scripting `.blend` files)

`.blend` files are **binary** — you cannot Read them directly. To inspect or modify
a `.blend`, drive Blender in background mode with a Python script.

### Binary and versions

- **Blender executable:** `/home/dk/Apps/blender/blender`  (Blender **5.1.2**)
- **Installed add-on (what Blender actually loads):**
  `~/.config/blender/5.1/scripts/addons/phobos/`
- **This repo (source of truth for edits):** `~/Apps/blender/phobos/phobos/`
  - The installed copy is a **separate copy, not a symlink**. When patching Phobos,
    edit **both** the repo and the installed copy, then **restart Blender** (Python
    files do not hot-reload).

### Invocation pattern

```bash
/home/dk/Apps/blender/blender --background <file.blend> --python <script.py> 2>&1
```

- `--background` (`-b`) runs without a GUI and quits when the script finishes.
- Operators run in EXEC context, so calls like
  `bpy.ops.phobos.create_collision_objects(property_colltype='cylinder')` run
  `execute()` directly and **bypass the invoke dialog** — pass operator props as kwargs.
- Tracebacks from operators print to **stderr** (the system console), which is why a
  failing action can look like "nothing happens" in the GUI. Capture with `2>&1`.
- `/tmp` is ephemeral — keep reusable scripts under `.claude/scripts/` if they should
  persist, or paste inline.

### Example: dump the scene / Phobos structure

Save as e.g. `.claude/scripts/dump_blend.py`:

```python
import bpy

objs = sorted(bpy.data.objects, key=lambda x: x.name)
print("Total objects:", len(objs))
for o in objs:
    cprops = {k: o[k] for k in o.keys() if k != "_RNA_UI"}
    print(f"- {o.name} | phobostype={getattr(o,'phobostype','?')} | "
          f"data={type(o.data).__name__ if o.data else None} | "
          f"parent={o.parent.name if o.parent else None} | "
          f"colls={[c.name for c in o.users_collection]}")
    for k, v in cprops.items():
        print(f"    {k} = {str(v)[:120]}")

print("\n=== TREE ===")
def walk(o, d=0):
    print("  "*d + f"{o.name} [{getattr(o,'phobostype','?')}]")
    for c in sorted(o.children, key=lambda x: x.name):
        walk(c, d+1)
for r in sorted([o for o in objs if o.parent is None], key=lambda x: x.name):
    walk(r)
```

Run:

```bash
/home/dk/Apps/blender/blender --background /home/dk/Repo/blender/urdf_test.blend \
  --python /home/dk/Apps/blender/phobos/.claude/scripts/dump_blend.py 2>&1
```

### Example: reproduce a Phobos operator failure headless

```python
import bpy, traceback
obj = bpy.data.objects["wheel2"]
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
try:
    print("RESULT:", bpy.ops.phobos.create_collision_objects(property_colltype='cylinder'))
except Exception:
    traceback.print_exc()
```

To **save** changes back, end the script with:
`bpy.ops.wm.save_as_mainfile(filepath="/path/out.blend")`
(make a backup copy first).

## Phobos object model (how a robot maps to Blender)

- A **link** = an **armature** object. Its name is the link name.
- The **joint** is stored **on the link armature** as custom props (`joint/name`,
  `joint/type`, `joint/axis`, `joint/limits/*`) — there is no separate joint object.
- **visual / collision / inertial** = **mesh** objects, each **parented to** their link
  armature, with matching `phobostype` and a `geometry/type` prop.
- Collections group by type: `link`, `visual`, `collision`, `inertial`. A new collision
  lands in the `collision` collection (and is drawn as wireframe inside the visual, so it
  can look invisible if that collection is hidden).
- `resource::*` objects (`joint_continuous`, `link_root`, …) are Phobos UI gizmos, not
  part of the robot — ignore them.

## Working sample model

`/home/dk/Repo/blender/urdf_test.blend` — `simple_amr_test` AMR:
`Base_link → steer1_link (revolute) → wheel1_link (continuous)`, mirrored for wheel 2.
Exported URDF lives at
`/home/dk/Repo/amr_urdf/simple_amr_test/urdf/simple_amr_test.urdf`.

> Note: Claude Code auto-loads a project CLAUDE.md from **either** `./CLAUDE.md`
> **or** `./.claude/CLAUDE.md` (both are recognized startup locations), so this file
> is loaded automatically — no symlink needed.
