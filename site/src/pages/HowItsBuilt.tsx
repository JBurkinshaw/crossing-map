import facts from 'virtual:site-facts'
import { Architecture } from './Architecture'
import { bytes, DATA_URL, layerLabel, REPO_URL } from './format'
import { Markdown } from './markdown'

// The project's real decision log, read at build time (plan section 4.3). The pattern is relative because
// a leading / would mean site/, the app root.
const files = import.meta.glob<string>('../../../docs/decisions/*.md', { query: '?raw', import: 'default', eager: true })

type DecisionRecord = { number: string; title: string; status: string; body: string }

const records: DecisionRecord[] = Object.entries(files)
  .filter(([path]) => /\/\d{4}-[^/]+\.md$/.test(path))
  .sort(([a], [b]) => a.localeCompare(b))
  .map(([, text]) => {
    const lines = text.split('\n')
    const [, number, title] = lines[0].match(/^# (\d+)\. (.*)$/) ?? ['', '', lines[0].replace(/^# /, '')]
    const meta = lines.slice(1, 5).filter((l) => /^(Status|Phase): /.test(l))
    const body = lines.slice(1).filter((l) => !meta.includes(l)).join('\n')
    return { number, title, status: meta.map((l) => l.replace(/^\w+: /, '')).join(' · '), body }
  })

function CountTable({ by, caption }: { by: 'certainty' | 'source' | 'method'; caption: string }) {
  const values = [...new Set(facts.layers.flatMap((l) => Object.keys(l[by])))].sort()
  return (
    <table>
      <caption>{caption}</caption>
      <thead>
        <tr>
          <th scope="col">{by}</th>
          {facts.layers.map((l) => (
            <th key={l.name} scope="col" className="num">
              {layerLabel(l.name)}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {values.map((v) => (
          <tr key={v}>
            <th scope="row">{v}</th>
            {facts.layers.map((l) => (
              <td key={l.name} className="num">
                {l[by][v] ?? ''}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export function HowItsBuilt() {
  const tileTotal = facts.tiles.reduce((sum, t) => sum + t.bytes, 0)
  return (
    <>
      <p className="lede">
        A static site: a folder of small GeoJSON files, a few PMTiles archives, and one outside tile service for
        the satellite view. No server, no database. Everything below is read from the project’s own files when the
        site is built, so it cannot drift from what the site does.
      </p>

      <h2>The shape of the system</h2>
      <Architecture />
      <p>
        The pipeline runs on the author’s machine, because it needs a copy of the book and hours of relief
        processing. It writes the story layers to the repository as GeoJSON, and the tile archives to a GitHub
        release, because they are too large for git. GitHub Actions checks the data against its schemas, builds the
        site, and deploys it to GitHub Pages, which answers the range requests PMTiles needs.
      </p>

      <h2>Decisions</h2>
      <p>
        Each decision is a short record: the problem, what was decided, what was rejected and why, and what follows.
        A record is not edited once accepted; a later one supersedes it. These are the {records.length} records in{' '}
        <a href={`${REPO_URL}/tree/main/docs/decisions`}>docs/decisions</a>, as they stand in this build.
      </p>
      <div className="records">
        {records.map((r) => (
          <details key={r.number} className="record">
            <summary>
              <span className="record-number">{r.number}</span> {r.title}
              <span className="meta"> {r.status}</span>
            </summary>
            <Markdown source={r.body} shift={1} />
          </details>
        ))}
      </div>

      <h2>Where the data comes from</h2>
      <p>
        Every feature carries its certainty, its source and the method that placed it. These counts are taken from
        the published files at build time.
      </p>
      <div className="tables">
        <CountTable by="certainty" caption="Features by certainty" />
        <CountTable by="source" caption="Features by source" />
        <CountTable by="method" caption="Features by method" />
      </div>
      <p>
        <strong>Accuracy targets.</strong> Located: within 250 m of the gazetteer feature. Approximate: the note says
        what the pin stands in for. Inferred: never smaller than the evidence. Sources are gazetteers (GNIS,
        GeoNames, Wikidata), lines the text names (USGS NHD rivers, Census TIGER roads, Natural Earth rivers), the
        Copernicus elevation model for summits, and this site’s own reading, marked <code>this-site</code>.
      </p>

      <h2>Numbers</h2>
      <table>
        <caption>Tile archives, from release {facts.tileRelease}</caption>
        <tbody>
          {facts.tiles.map((t) => (
            <tr key={t.file}>
              <th scope="row">
                <code>{t.file}</code>
              </th>
              <td className="num">{bytes(t.bytes)}</td>
            </tr>
          ))}
          <tr className="total">
            <th scope="row">All tiles</th>
            <td className="num">{bytes(tileTotal)}</td>
          </tr>
        </tbody>
      </table>
      <table>
        <caption>The rest</caption>
        <tbody>
          <tr>
            <th scope="row">Published data (data/, both formats)</th>
            <td className="num">{bytes(facts.dataBytes)}</td>
          </tr>
        </tbody>
      </table>

      <h2>Links</h2>
      <ul>
        <li>
          <a href={REPO_URL}>The repository</a>, with the pipeline, the site and the plan.
        </li>
        <li>
          <a href="#/data">The data downloads</a> and their <a href={`${DATA_URL}schema/story-layer.schema.json`}>JSON Schema</a>.
        </li>
        <li>
          <a href="#/credits">Credits</a> for every source.
        </li>
      </ul>
    </>
  )
}
