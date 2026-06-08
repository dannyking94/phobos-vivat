import bpy

print("\n===== OBJECTS =====")
objs = list(bpy.data.objects)
print("Total objects:", len(objs))

def phobostype(o):
    return getattr(o, "phobostype", "<none>")

# Build child map
for o in sorted(objs, key=lambda x: x.name):
    p = o.parent
    print(f"\n- {o.name}")
    print(f"    phobostype : {phobostype(o)}")
    print(f"    data type  : {type(o.data).__name__ if o.data else None}")
    print(f"    parent     : {p.name if p else None}")
    print(f"    collections: {[c.name for c in o.users_collection]}")
    loc = o.location
    print(f"    location   : ({loc.x:.5f}, {loc.y:.5f}, {loc.z:.5f})")
    # custom props (skip internal _RNA_UI)
    cprops = {k: o[k] for k in o.keys() if k != "_RNA_UI"}
    if cprops:
        print(f"    custom props:")
        for k, v in cprops.items():
            sv = str(v)
            if len(sv) > 120:
                sv = sv[:120] + "..."
            print(f"        {k} = {sv}")

print("\n===== PARENT/CHILD TREE =====")
roots = [o for o in objs if o.parent is None]
def walk(o, depth=0):
    print("  " * depth + f"{o.name} [{phobostype(o)}]")
    for c in sorted(o.children, key=lambda x: x.name):
        walk(c, depth + 1)
for r in sorted(roots, key=lambda x: x.name):
    walk(r)

print("\n===== COLLECTIONS =====")
for c in bpy.data.collections:
    print(f"- {c.name}: {[o.name for o in c.objects]}")

print("\n===== MATERIALS =====")
for m in bpy.data.materials:
    print(f"- {m.name}")

print("\n===== DONE =====")
