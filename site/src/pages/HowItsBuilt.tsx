import { useState } from 'react'
import facts from 'virtual:site-facts'
import { CERTAINTY_LABEL } from '../panel/certainty'
import { Architecture } from './Architecture'
import { bytes, DATA_URL, layerLabel, REPO_URL, repoUrl } from './format'
import { Markdown } from './markdown'

// The project's real decision log, read at build time (design section 4.3). The pattern is relative because
// a leading / would mean site/, the app root.
const files = import.meta.glob<string>('../../../docs/decisions/[0-9]*.md', { query: '?raw', import: 'default', eager: true })

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

// In place of the records while spoilers are hidden: what they hold, and a way to show them for this visit that
// confirms first, as "Show everything" does. The reader's progress is left as it is.
function RecordsHidden({ onShow }: { onShow: () => void }) {
  const [confirming, setConfirming] = useState(false)
  return (
    <div className="records-hidden">
      <p>
        The records name places and events from the whole book, so they are hidden while the map hides what you have
        not read yet.
      </p>
      {confirming ? (
        <div className="progress-confirm">
          <p>Show the decision records? They name places and events from the whole book, the ending included.</p>
          <div className="progress-actions">
            {/* oxlint-disable-next-line jsx-a11y/no-autofocus */}
            <button type="button" autoFocus onClick={onShow}>
              Show the records
            </button>
            <button type="button" onClick={() => setConfirming(false)}>
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="progress-actions">
          <button type="button" onClick={() => setConfirming(true)}>
            Show the decision records
          </button>
        </div>
      )}
    </div>
  )
}

// `spoilers`: the map is hiding what the reader has not reached, so the decision records, which name places and
// events from the whole book, wait behind a warning (design section 11: nothing later shows anywhere).
export function HowItsBuilt({ spoilers }: { spoilers: boolean }) {
  const [shown, setShown] = useState(false)
  const measured = facts.tiles.every((t) => t.bytes !== null)
  const tileTotal = facts.tiles.reduce((sum, t) => sum + (t.bytes ?? 0), 0)
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
        <a href={repoUrl('docs/decisions')}>docs/decisions</a>, as they stand in this build.
      </p>
      {spoilers && !shown ? (
        <RecordsHidden onShow={() => setShown(true)} />
      ) : (
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
      )}

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
        The tables show the data’s own values. The map’s cards and the About page give each certainty a plain name:{' '}
        {Object.entries(CERTAINTY_LABEL).map(([value, label], i, all) => (
          <span key={value}>
            <code>{value}</code> is “{label}”{i < all.length - 1 ? '; ' : '.'}
          </span>
        ))}
      </p>
      <p>
        <strong>Accuracy targets.</strong> Located: within 250 m of the gazetteer feature. Approximate: the note says
        what the pin stands in for. Inferred: never smaller than the evidence. Sources are gazetteers (GNIS,
        GeoNames, Wikidata), lines the text names (USGS NHD rivers, Census TIGER roads, Natural Earth rivers), the
        Copernicus elevation model for summits, and this site’s own reading, marked <code>this-site</code>.
      </p>

      <h2>Inferred areas</h2>
      <p>
        Where the book gives no name, a stop gets a circle as wide as the clues allow. Most circles are then cut to
        the ground the stop’s reasoning describes: a river and its banks, a valley floor, a road’s verge, the flat
        of a playa, the side of a border line. Each cut is a short rule run on open data (the Copernicus elevation
        model, INEGI and USGS rivers, Census roads), written out on the area’s card. A rule is not a surveyor: it
        draws the ground the clue points to, not the place itself, and an escarpment or a ridge comes out in broken
        pieces. No area grows beyond its circle. No open map of the 1940s roads in Chihuahua and Sonora was found, so
        where the book puts a camp on an old road there, a straight line between the towns stands in for the road;
        the old roads need a historical source. One large region is drawn from the elevation model, not from its
        real boundary, until a period map of it is found. Any area can be redrawn when a
        reader brings more: each card has a link to suggest a correction (decision 0020).
      </p>

      <h2>Modelled routes</h2>
      <p>
        The book seldom says which way a rider went between two stops. Where it names the road or river, the route
        follows today’s line of it: Census roads and USGS rivers in the US, INEGI’s roads and rivers in Mexico,
        taken the shortest way along them between the stops. Each leg’s card says, under “How this line was drawn”,
        which line it follows and how. Where the book does not, most legs are drawn as gentle curves, which say
        only that the way is unknown.
        Across the sierras and up the long valleys a curve reads badly, so those legs are modelled: the line is the
        way of least effort between the two stops over the ground, for a rider at a walk (or, on the first
        journey, a wolf on foot). The model works on a 90 m grid of the Copernicus elevation model. A horse’s speed
        falls with the slope by Tobler’s hiking function, about 6 km/h on the flat; steep ground and canyon walls
        cost more; crossing a river costs a few minutes by its size; lakes are boggy; and where the book has the
        rider on a road or a river trail, the line is drawn towards INEGI’s dirt tracks, the old railway, or the
        river. A rider in Mexico crosses the border only where the book does.
      </p>
      <p>
        A modelled line is a plausible way, not the one taken. The weights are judgements: on about a dozen legs a
        different weighting moves the line by 5 km or more, and today’s tracks only stand in for the roads of the
        1940s. Flat legs, and legs the book tells in a sentence as weeks of riding, stay curves, because the model
        has nothing to add there. The model also checks the story: on one leg, the book’s timing asks a horse
        for about 100 km in a day, some 16 hours at a walk by the model, which is listed as an open question
        (decision 0021).
      </p>

      <h2>Mountain glyphs</h2>
      <p>
        The little drawn mountains are found from the ground, not copied from a map. The Copernicus elevation model
        is read on a 200 m grid, keeping the highest point in each cell so that summits survive. For every summit the
        build measures its prominence: how far you would have to come down from it before you could climb to any
        higher ground. A summit standing at least 200 m above its surroundings in that sense gets a glyph; one of
        600 m or more gets a medium glyph, and 1,000 m or more a large one. So a glyph says how much a mountain
        stands out from the country round it, not how high it is above the sea.
      </p>
      <p>
        Each summit takes the name of the nearest summit, hill, mesa or ridge in the US and Mexican gazetteers (GNIS
        and GeoNames) within 2 km, and the name decides the drawing: a Mesa or a Butte is drawn flat-topped, and
        cones, domes and ridges have their own drawings; a summit whose name does not say is drawn as a peak. Named mesas, buttes and cones are kept down to 100 m of
        prominence, because few of them stand higher. Passes are the low points between two summits where the ground
        rises on both sides; named ones are lettered across the saddle, unnamed ones get a small pass glyph. The
        height beside a summit is the elevation model’s, so it can differ by some metres from a surveyed height.
        Each glyph is one of a dozen hand-drawn variants, flipped, scaled and turned a little by a fixed rule, so
        the same mountain always looks the same. A glyph marks where a summit is; its outline is a symbol, not a
        portrait of that mountain.
      </p>

      <h2>Caveats</h2>
      <p>
        <strong>Springs, ranches and stations.</strong> The springs, ranches, stations and tanks along the journeys
        come from today’s gazetteers: GNIS in the US and GeoNames in Mexico. Neither says when a place was founded,
        so some of the ranches in particular, about 480 of them from GeoNames, may be younger than the 1940s. They
        are drawn because dry country is read by its water and its ranches, as the Wheeler sheets read it, not
        because each one is known to have stood in the book’s years. The ranches and springs the book itself names
        are drawn separately, with its own spelling.
      </p>
      <p>
        <strong>Forts, mines, ghost towns and the rest.</strong> The other period places along the journeys (forts and
        army air fields, ghost towns and abandoned places, mines, sawmills, churches, cemeteries, schools, old post
        offices, corrals, camps, named wells and windmills) come from the same gazetteers and from the GNIS file of
        2021, and none of them is dated. Where a gazetteer marks a place as historical or abandoned, it does not say
        when it was given up, so a place may be drawn that was already gone by 1939, or not yet gone. Town churches and
        schools, numbered wells and anything plainly modern are left out.
      </p>
      <p>
        <strong>Today’s ground.</strong> Rivers, creeks, lakes and the relief come from present-day surveys (USGS,
        INEGI, Copernicus). Modern earth dams are left out of the gazetteer places, but a river or a lake is drawn
        as it is now, which may not be quite where it was then.
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
              <td className="num">{t.bytes === null ? 'not in this build' : bytes(t.bytes)}</td>
            </tr>
          ))}
          {measured && (
            <tr className="total">
              <th scope="row">All tiles</th>
              <td className="num">{bytes(tileTotal)}</td>
            </tr>
          )}
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
          <a href={REPO_URL}>The repository</a>, with the pipeline, the site and the design.
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
