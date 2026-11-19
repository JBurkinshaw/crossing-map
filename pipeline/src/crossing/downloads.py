"""Write a GeoParquet copy of each published story layer, for download (decision 0009).

Run from the repo root: uv run --project pipeline python -m crossing.downloads
With --check, write nothing and exit non-zero if any copy no longer matches its GeoJSON.
`crossing.build_story` and `crossing.build_vignettes` also write each layer's copy with the layer.

Each layer in data/ becomes data/parquet/<layer>.parquet: one row per feature, one column per property,
and the geometry as WKB in a `geometry` column, with GeoParquet 1.1 metadata (WGS 84, the default CRS).
Column types come from the story-layer JSON Schema, so a property that is null throughout a layer
keeps its type.
"""

import json
import sys

import pyarrow as pa
import pyarrow.parquet as pq
import shapely

from crossing.paths import DATA, REPO
from crossing.validate import LAYERS

OUT = DATA / "parquet"
SCHEMA = DATA / "schema" / "story-layer.schema.json"
GEOPARQUET_VERSION = "1.1.0"


def arrow_type(spec: dict) -> pa.DataType:
    """The Arrow type for one property of the JSON Schema."""
    if "enum" in spec:
        kinds = {type(v).__name__ for v in spec["enum"] if v is not None}
        return pa.string() if kinds == {"str"} else pa.int64()
    if "oneOf" in spec or "$ref" in spec:
        return pa.string()  # episode references: strings such as 1-09
    kinds = spec["type"] if isinstance(spec["type"], list) else [spec["type"]]
    kind = next(k for k in kinds if k != "null")
    if kind == "array":
        items = spec.get("items", {})
        if items.get("type") == "object":  # a list of records, such as leads: a field for each of their properties
            return pa.list_(pa.struct([pa.field(k, arrow_type(v)) for k, v in items["properties"].items()]))
        return pa.list_(pa.string())
    return {"string": pa.string(), "integer": pa.int64(), "number": pa.float64(), "boolean": pa.bool_()}[kind]


def layer_table(name: str, props_schema: dict) -> pa.Table:
    doc = json.loads((DATA / f"{name}.geojson").read_text(encoding="utf-8"))
    features = doc["features"]
    # The layer's own columns, in the order its features first use them.
    columns: list[str] = []
    for f in features:
        columns += [k for k in f["properties"] if k not in columns]
    fields = [pa.field(c, arrow_type(props_schema[c])) for c in columns]
    geoms = [shapely.geometry.shape(f["geometry"]) for f in features]
    arrays = [pa.array([f["properties"].get(c) for f in features], type=fld.type)
              for c, fld in zip(columns, fields, strict=True)]
    arrays.append(pa.array(shapely.to_wkb(geoms, output_dimension=2), type=pa.binary()))
    fields.append(pa.field("geometry", pa.binary()))
    xmin, ymin, xmax, ymax = shapely.total_bounds(geoms)
    geo = {
        "version": GEOPARQUET_VERSION,
        "primary_column": "geometry",
        "columns": {
            "geometry": {
                "encoding": "WKB",
                "geometry_types": sorted({g.geom_type for g in geoms}),
                "bbox": [round(v, 5) for v in (xmin, ymin, xmax, ymax)],
            }
        },
    }
    schema = pa.schema(fields, metadata={"geo": json.dumps(geo)})
    return pa.Table.from_arrays(arrays, schema=schema)


def properties_schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"]["properties"]["properties"]


def write_copy(name: str) -> None:
    """Write data/parquet/<name>.parquet from data/<name>.geojson."""
    table = layer_table(name, properties_schema())
    OUT.mkdir(exist_ok=True)
    path = OUT / f"{name}.parquet"
    pq.write_table(table, path, compression="zstd")
    print(f"{path.relative_to(REPO)}: {table.num_rows} rows, {path.stat().st_size:,} bytes")


def main() -> None:
    check = "--check" in sys.argv[1:]
    props_schema = properties_schema()
    stale = []
    for name in LAYERS:
        if not check:
            write_copy(name)
            continue
        table = layer_table(name, props_schema)
        path = OUT / f"{name}.parquet"
        current = pq.read_table(path) if path.exists() else None
        same_geo = current is not None and current.schema.metadata.get(b"geo") == table.schema.metadata[b"geo"]
        if current is None or not current.equals(table) or not same_geo:
            stale.append(path.relative_to(REPO))
    if stale:
        print("Out of date; run uv run --project pipeline python -m crossing.downloads:", *stale, sep="\n  ")
        sys.exit(1)


if __name__ == "__main__":
    main()
