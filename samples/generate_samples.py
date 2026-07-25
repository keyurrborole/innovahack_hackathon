"""
Generate sample 3D .obj models for the GNN Pipeline demo.
No external dependencies — uses only Python stdlib math.
"""
import math
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def write_obj(filepath: str, vertices: list, faces: list, name: str = "object"):
    """Write vertices and triangular faces to a Wavefront .obj file."""
    with open(filepath, "w") as f:
        f.write(f"# Sample model: {name}\n")
        f.write(f"# Vertices: {len(vertices)}  Faces: {len(faces)}\n")
        f.write(f"o {name}\n\n")
        for v in vertices:
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        f.write("\n")
        for face in faces:
            # OBJ faces are 1-indexed
            f.write("f " + " ".join(str(i + 1) for i in face) + "\n")
    print(f"  [OK] {os.path.basename(filepath):30s}  verts={len(vertices):>5}  faces={len(faces):>5}")


# ── 1. Cube ──────────────────────────────────────────────────────────────────
def make_cube():
    s = 1.0
    verts = [
        (-s, -s, -s), ( s, -s, -s), ( s,  s, -s), (-s,  s, -s),
        (-s, -s,  s), ( s, -s,  s), ( s,  s,  s), (-s,  s,  s),
    ]
    quads = [
        (0,1,2,3), (4,7,6,5), (0,4,5,1),
        (2,6,7,3), (0,3,7,4), (1,5,6,2),
    ]
    tris = []
    for q in quads:
        tris.append((q[0], q[1], q[2]))
        tris.append((q[0], q[2], q[3]))
    return verts, tris


# ── 2. UV Sphere ─────────────────────────────────────────────────────────────
def make_sphere(stacks=16, slices=32, radius=1.0):
    verts = [(0, radius, 0)]  # top pole
    for i in range(1, stacks):
        phi = math.pi * i / stacks
        for j in range(slices):
            theta = 2 * math.pi * j / slices
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.cos(phi)
            z = radius * math.sin(phi) * math.sin(theta)
            verts.append((x, y, z))
    verts.append((0, -radius, 0))  # bottom pole

    faces = []
    # Top cap
    for j in range(slices):
        faces.append((0, 1 + j, 1 + (j + 1) % slices))
    # Body
    for i in range(stacks - 2):
        for j in range(slices):
            curr = 1 + i * slices + j
            nxt  = 1 + i * slices + (j + 1) % slices
            below_curr = curr + slices
            below_nxt  = nxt + slices
            faces.append((curr, below_curr, below_nxt))
            faces.append((curr, below_nxt, nxt))
    # Bottom cap
    bottom = len(verts) - 1
    base = 1 + (stacks - 2) * slices
    for j in range(slices):
        faces.append((bottom, base + (j + 1) % slices, base + j))

    return verts, faces


# ── 3. Torus ─────────────────────────────────────────────────────────────────
def make_torus(major_seg=32, minor_seg=16, R=1.0, r=0.4):
    verts = []
    for i in range(major_seg):
        theta = 2 * math.pi * i / major_seg
        for j in range(minor_seg):
            phi = 2 * math.pi * j / minor_seg
            x = (R + r * math.cos(phi)) * math.cos(theta)
            y = r * math.sin(phi)
            z = (R + r * math.cos(phi)) * math.sin(theta)
            verts.append((x, y, z))

    faces = []
    for i in range(major_seg):
        for j in range(minor_seg):
            a = i * minor_seg + j
            b = i * minor_seg + (j + 1) % minor_seg
            c = ((i + 1) % major_seg) * minor_seg + (j + 1) % minor_seg
            d = ((i + 1) % major_seg) * minor_seg + j
            faces.append((a, d, c))
            faces.append((a, c, b))
    return verts, faces


# ── 4. Diamond Tower (architectural shape) ───────────────────────────────────
def make_diamond_tower(levels=5, base_radius=1.0, height=3.0):
    """A stacked octahedral tower — interesting topology for GNN processing."""
    verts = []
    faces = []
    slices = 8
    level_h = height / levels

    for lvl in range(levels + 1):
        y = lvl * level_h
        # Alternate radius for diamond pinch effect
        if lvl % 2 == 0:
            rad = base_radius
        else:
            rad = base_radius * 0.5
        for s in range(slices):
            angle = 2 * math.pi * s / slices
            verts.append((rad * math.cos(angle), y, rad * math.sin(angle)))

    # Connect levels
    for lvl in range(levels):
        for s in range(slices):
            a = lvl * slices + s
            b = lvl * slices + (s + 1) % slices
            c = (lvl + 1) * slices + (s + 1) % slices
            d = (lvl + 1) * slices + s
            faces.append((a, b, c))
            faces.append((a, c, d))

    # Cap bottom
    bottom_center = len(verts)
    verts.append((0, 0, 0))
    for s in range(slices):
        faces.append((bottom_center, s, (s + 1) % slices))

    # Cap top
    top_center = len(verts)
    verts.append((0, height, 0))
    top_base = levels * slices
    for s in range(slices):
        faces.append((top_center, top_base + (s + 1) % slices, top_base + s))

    return verts, faces


# ── 5. Geodesic Sphere (Icosphere subdivided) ────────────────────────────────
def make_icosphere(subdivisions=2, radius=1.0):
    """Icosahedron subdivided — produces even triangulation, great for GNN."""
    t = (1.0 + math.sqrt(5.0)) / 2.0
    verts = [
        (-1,  t,  0), ( 1,  t,  0), (-1, -t,  0), ( 1, -t,  0),
        ( 0, -1,  t), ( 0,  1,  t), ( 0, -1, -t), ( 0,  1, -t),
        ( t,  0, -1), ( t,  0,  1), (-t,  0, -1), (-t,  0,  1),
    ]
    faces = [
        (0,11,5),(0,5,1),(0,1,7),(0,7,10),(0,10,11),
        (1,5,9),(5,11,4),(11,10,2),(10,7,6),(7,1,8),
        (3,9,4),(3,4,2),(3,2,6),(3,6,8),(3,8,9),
        (4,9,5),(2,4,11),(6,2,10),(8,6,7),(9,8,1),
    ]

    # Normalize initial vertices to the sphere
    norm_verts = []
    for v in verts:
        l = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
        norm_verts.append((v[0]/l * radius, v[1]/l * radius, v[2]/l * radius))
    verts = norm_verts

    midpoint_cache = {}

    def get_midpoint(v1_idx, v2_idx):
        key = (min(v1_idx, v2_idx), max(v1_idx, v2_idx))
        if key in midpoint_cache:
            return midpoint_cache[key]
        p1, p2 = verts[v1_idx], verts[v2_idx]
        mid = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2, (p1[2]+p2[2])/2)
        l = math.sqrt(mid[0]**2 + mid[1]**2 + mid[2]**2)
        mid = (mid[0]/l * radius, mid[1]/l * radius, mid[2]/l * radius)
        idx = len(verts)
        verts.append(mid)
        midpoint_cache[key] = idx
        return idx

    for _ in range(subdivisions):
        new_faces = []
        midpoint_cache = {}
        for tri in faces:
            a = get_midpoint(tri[0], tri[1])
            b = get_midpoint(tri[1], tri[2])
            c = get_midpoint(tri[2], tri[0])
            new_faces.append((tri[0], a, c))
            new_faces.append((tri[1], b, a))
            new_faces.append((tri[2], c, b))
            new_faces.append((a, b, c))
        faces = new_faces

    return verts, faces


# ── Generate all models ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n  Generating sample 3D models for GNN Pipeline...\n")

    write_obj(os.path.join(OUTPUT_DIR, "cube.obj"),
              *make_cube(), name="Cube")

    write_obj(os.path.join(OUTPUT_DIR, "sphere_hires.obj"),
              *make_sphere(stacks=24, slices=48), name="HiResSphere")

    write_obj(os.path.join(OUTPUT_DIR, "torus.obj"),
              *make_torus(major_seg=36, minor_seg=20), name="Torus")

    write_obj(os.path.join(OUTPUT_DIR, "diamond_tower.obj"),
              *make_diamond_tower(levels=8, base_radius=1.0, height=4.0),
              name="DiamondTower")

    write_obj(os.path.join(OUTPUT_DIR, "icosphere.obj"),
              *make_icosphere(subdivisions=3, radius=1.0), name="Icosphere")

    print(f"\n  [DONE] All models saved to: {OUTPUT_DIR}\n")
