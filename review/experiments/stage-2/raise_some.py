"""Re-raise only the story features that changed, splicing them into data/raised/ (the full plan_oblique run takes
hours). Uses the same strips' smoothed DEMs and base height 0.0 as the published run."""
import json
import tempfile
from pathlib import Path

from shapely.geometry import shape
from shapely.ops import transform

from crossing import plan_oblique as po

DATA = Path("data")
BEFORE = Path(".scratch/before")
changed: dict[str, set] = {}
geoms = []
for name in po.STORY:
    old = {f["properties"]["id"]: f for f in json.loads((BEFORE / f"{name}.geojson").read_text())["features"]}
    for f in json.loads((DATA / f"{name}.geojson").read_text())["features"]:
        i = f["properties"]["id"]
        if i not in old or old[i]["geometry"] != f["geometry"]:
            changed.setdefault(name, set()).add(i)
            geoms.append(shape(f["geometry"]))
print({k: sorted(v) for k, v in changed.items()})
# A check feature: unchanged, near Cloverdale; its re-raised point must match the published one.
CHECK = ("stops", "j2-cloverdale")

area = po.strips()
xs = []
for g in geoms:
    xs.append(transform(po.to_utm, g).bounds)
minx, miny = min(b[0] for b in xs), min(b[1] for b in xs)
maxx, maxy = max(b[2] for b in xs), max(b[3] for b in xs)
mine = [s for s in area if s["core"][0] <= maxx and s["core"][2] >= minx and s["core"][1] <= maxy and s["core"][3] >= miny]
print(len(mine), "strips of", len(area))
with tempfile.TemporaryDirectory() as folder:
    tmp = Path(folder)
    dems = []
    for s in mine:
        dem = tmp / f"{s['name']}.tif"
        po.prepare_dem(s["bounds"], po.CELL, dem)
        dems.append(dem)
    heights = po.Heights(list(zip(mine, dems)), 0.0, tmp)
    out = tmp / "raised"
    po.RAISED_DATA = out
    po.raise_story(heights)
    for name in po.STORY:
        pub_path = DATA / "raised" / f"{name}.geojson"
        pub = json.loads(pub_path.read_text())
        fresh = {f["properties"]["id"]: f for f in json.loads((out / f"{name}.geojson").read_text())["features"]}
        if name == CHECK[0]:
            a = next(f for f in pub["features"] if f["properties"]["id"] == CHECK[1])["geometry"]["coordinates"]
            print("check", CHECK[1], "published", a, "re-raised", fresh[CHECK[1]]["geometry"]["coordinates"])
        flat = {f["properties"]["id"]: f for f in json.loads((DATA / f"{name}.geojson").read_text())["features"]}
        ids = [f["properties"]["id"] for f in pub["features"]]
        feats = []
        # Keep the published order and geometry; take the new properties; new geometry only where it changed.
        for i in [f["properties"]["id"] for f in fresh.values()]:
            f = next((p for p in pub["features"] if p["properties"]["id"] == i), None)
            if f is None or i in changed.get(name, set()):
                feats.append(fresh[i])
            else:
                feats.append({**f, "properties": flat[i]["properties"]})
        pub["features"] = feats
        pub_path.write_text(json.dumps(pub, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(name, len(ids), "->", len(feats))
