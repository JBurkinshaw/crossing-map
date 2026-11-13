import facts from 'virtual:site-facts'
import { bytes, DATA_URL, layerLabel, REPO_URL } from './format'

const LAYERS: Record<string, string> = {
  places: 'Named places with a known location: stops, places passed, places in tales, and context towns.',
  stops: 'Each stop of each journey, in order. A stop refers to the place or area it stands for.',
  areas: 'Inferred places drawn as areas (cabins, camps, graves, unnamed settlements), each with its reasoning.',
  journeys: 'Route segments between consecutive stops, for all seven journeys.',
  mountain_glyphs: 'Summits and passes found in the Copernicus elevation model, named from GNIS and GeoNames.',
}

// What each shared property means (plan section 6); the schema's own descriptions are used where it has them.
const FIELDS: Record<string, string> = {
  id: 'Stable identifier.',
  name: 'Name used on the map.',
  kind: 'What the feature is: town, ranch, river crossing, route segment, peak and so on.',
  characters: 'Who is there or travels the segment.',
  journey: 'Journey J1 to J7.',
  sequence: 'Order within the journey.',
  part: 'Part of the novel, 1 to 4.',
  episode: 'Part and episode where it happens, for example 1-09.',
  first_seen: 'The earliest episode in which the feature may appear.',
  certainty: 'located, approximate, inferred or reported (see the About page).',
  uncertainty_m: 'Rough radius of doubt, in metres.',
  method: 'How the geometry was made: gazetteer match, computed, hand-drawn, a path the text names, modelled, schematic curve, or generated from elevation.',
  source: 'Where the geometry or name came from.',
  source_id: 'The feature’s identifier in that source.',
  source_licence: 'The licence of that source.',
  note_safe: 'A short note in our own words that gives nothing away.',
  reasoning: 'For inferred features: the clues used, in plain words.',
}

function typeLabel(type: string | string[] | null, values: unknown[] | null): string {
  if (values) return `one of ${values.map((v) => (v === null ? 'null' : String(v))).join(', ')}`
  const kinds = (Array.isArray(type) ? type : [type ?? 'text']).map((k) => (k === 'array' ? 'list of text' : k === 'string' ? 'text' : k))
  return kinds.join(' or ')
}

export function Data() {
  return (
    <>
      <p className="lede">
        Everything on the map is open data. The story layers are free to reuse under{' '}
        <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>; each feature’s{' '}
        <code>source_licence</code> gives the terms of the source it came from.
      </p>

      <h2>Downloads</h2>
      <p>
        Each layer comes in two formats made from one source. GeoJSON (WGS 84, RFC 7946) opens anywhere. GeoParquet
        is the same data, one row per feature, for DuckDB, GeoPandas and QGIS.
      </p>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">Layer</th>
              <th scope="col" className="num">Features</th>
              <th scope="col">Geometry</th>
              <th scope="col">GeoJSON</th>
              <th scope="col">GeoParquet</th>
            </tr>
          </thead>
          <tbody>
            {facts.layers.map((l) => (
              <tr key={l.name}>
                <th scope="row">
                  {layerLabel(l.name)}
                  <div className="meta">{LAYERS[l.name]}</div>
                </th>
                <td className="num">{l.features.toLocaleString('en')}</td>
                <td>{l.geometry.join(', ')}</td>
                <td>
                  <a href={`${DATA_URL}${l.name}.geojson`} download>
                    {l.name}.geojson
                  </a>{' '}
                  <span className="meta">{bytes(l.geojsonBytes)}</span>
                </td>
                <td>
                  <a href={`${DATA_URL}parquet/${l.name}.parquet`} download>
                    {l.name}.parquet
                  </a>{' '}
                  <span className="meta">{bytes(l.parquetBytes)}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p>Also published:</p>
      <ul>
        {facts.files.map((f) => (
          <li key={f.file}>
            <a href={`${DATA_URL}${f.file}`} download>
              {f.file}
            </a>{' '}
            <span className="meta">{bytes(f.bytes)}</span>:{' '}
            {f.file === 'episodes.json'
              ? 'the novel’s 41 episodes, with their opening words and length.'
              : 'places the book names that lie beyond the map.'}
          </li>
        ))}
        <li>
          <a href={`${DATA_URL}README.md`}>README.md</a>: each layer’s sources and licence.{' '}
          <a href={`${DATA_URL}LICENSE`}>LICENSE</a>: CC BY 4.0.
        </li>
        <li>
          <a href={`${DATA_URL}schema/story-layer.schema.json`}>story-layer.schema.json</a> and{' '}
          <a href={`${DATA_URL}schema/episodes.schema.json`}>episodes.schema.json</a>: the JSON Schemas every
          file is checked against.
        </li>
        <li>
          <code>raised/</code> <span className="meta">{bytes(facts.raisedBytes)}</span>: the story layers as drawn in
          the Raised view, shifted north with the height of the ground. Use the layers above for analysis.
        </li>
      </ul>

      <h2>Reading the GeoParquet files</h2>
      <p>
        Each file holds one layer. The geometry is a WKB column called <code>geometry</code>, in WGS 84, with
        GeoParquet 1.1 metadata, so tools read it as a spatial layer:
      </p>
      <pre>
        <code>
          {`# DuckDB
INSTALL spatial; LOAD spatial;
SELECT name, certainty, ST_AsText(geometry) FROM 'places.parquet';

# GeoPandas
import geopandas
places = geopandas.read_parquet("places.parquet")`}
        </code>
      </pre>
      <p>QGIS opens the files directly, as it does any vector layer, when its GDAL has the Parquet driver.</p>

      <h2>Schemas</h2>
      <p>
        Every story layer shares one property schema. A layer uses the properties below; in GeoParquet each is a
        column of the same name, and lists are list columns. Starred properties are required.
      </p>
      {facts.layers.map((l) => (
        <details key={l.name} className="record">
          <summary>{layerLabel(l.name)}</summary>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th scope="col">Property</th>
                  <th scope="col">Type</th>
                  <th scope="col">Meaning</th>
                </tr>
              </thead>
              <tbody>
                {l.columns.map((c) => (
                  <tr key={c.name}>
                    <th scope="row">
                      <code>{c.name}</code>
                      {c.required ? ' *' : ''}
                    </th>
                    <td>{typeLabel(c.type, c.values)}</td>
                    <td>{c.description ?? FIELDS[c.name] ?? ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      ))}
      <p>
        The pipeline that builds these files is in the <a href={REPO_URL}>repository</a>.
      </p>
    </>
  )
}
