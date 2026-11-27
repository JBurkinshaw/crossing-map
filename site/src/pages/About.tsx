import { COUNTING } from '../analytics'
import { showIntroduction } from '../welcome/showIntroduction'
import { CERTAINTY_LABEL } from '../panel/certainty'
import { FEEDBACK_FORM, feedbackUrl, REPO_URL } from './format'

export function About() {
  const form = feedbackUrl({ kind: 'general' })
  return (
    <>
      {/* The working blurb from docs/design.md (section 1). */}
      <p className="lede">
        I read <cite>All the Pretty Horses</cite> years ago, and only recently got to <cite>The Crossing</cite>. It left
        me wanting to know the country its characters travel through, and the geographer in me needed to see these
        places more closely. <cite>The Crossing</cite> moves through real
        country on both sides of the border. This is a map of where Billy, Boyd,
        “the girl” and the she-wolf went, built from real geographic data and marked honestly where the book leaves
        us guessing.
      </p>

      <p>
        <button type="button" className="link" onClick={showIntroduction}>
          Show the introduction again
        </button>
      </p>

      <h2>Why a map</h2>
      <p>
        <cite>The Crossing</cite> is a book about places as much as people. McCarthy names real towns, rivers,
        mountain ranges, ranches and border crossings, in English and in Spanish. A geographer would call these place
        names toponyms, and the book is packed with them. He measures the country the way a rider does: in days on
        horseback, a creek followed upstream, the lights of a town seen in the dark.
      </p>
      <p>
        But the book has no map. Every reader builds one in their head, and it’s easy to get lost. The journeys run
        from a single canyon to hundreds of miles of desert, and the book gives directions and distances only now and
        then. This site draws that map. Where the book names a place, it gets a pin on the real spot. Where the book
        only describes one, the map shows the area it could be in. It’s one reader’s best guess, not McCarthy’s own
        map, and it says where it isn’t sure.
      </p>

      <h2>How to use it</h2>
      <ol>
        <li>
          Tell the map how far you’ve read. It hides everything after that point, and you can change it any time from
          the reading-progress button in the panel.
        </li>
        <li>
          Pick a journey and press <strong>Next</strong> to follow it stop by stop.
        </li>
        <li>Tap anything on the map, such as a place or a route, to read about it.</li>
      </ol>
      <p>
        The book has four Parts and no chapter titles. This site splits each Part into episodes where McCarthy starts a
        new scene, and names each episode by the words it opens with, which the book sets in capitals: ‘They
        crossed…’. A stop’s card names its episode and sums it up, then says what happens at the stop itself.
      </p>

      <h2>How sure is each place?</h2>
      <p>Every place, route and area says how sure the map is about it.</p>
      {/* The names match the cards (panel/certainty.ts); How it's built maps them to the data's values. */}
      <ul>
        <li>
          <strong>{CERTAINTY_LABEL.located}:</strong> the book names the place, and it’s on today’s maps.
        </li>
        <li>
          <strong>{CERTAINTY_LABEL.approximate}:</strong> the pin stands in for something bigger, like a mountain
          range marked at its highest point.
        </li>
        <li>
          <strong>{CERTAINTY_LABEL.inferred}:</strong> the book doesn’t name the place, so the map shows the area its
          clues point to. The reasoning is on the card.
        </li>
        <li>
          <strong>{CERTAINTY_LABEL.reported}:</strong> a character tells of it, and the book gives nothing more.
        </li>
      </ul>
      <p>Routes are drawn in three ways:</p>
      {/* As the layer key draws them (map/tokens.ts, routeLines; decision 0033). */}
      <ul>
        <li>
          <strong>Solid</strong> where they follow a road or river the book names.
        </li>
        <li>
          <strong>Long dashes</strong> where this site has worked out a likely way over the ground.
        </li>
        <li>
          <strong>Short dashes</strong> where the line only joins the stops.
        </li>
      </ul>
      {FEEDBACK_FORM && (
        <p>
          If you know better, whether from a page of the book, an old map or the ground itself, every card has a link to
          suggest a correction.
        </p>
      )}

      <h2>About the text</h2>
      <p>
        The notes are in this site’s own words, and the site doesn’t reproduce the novel. Much of the dialogue is in
        Spanish, and every Spanish line has the site’s own English translation, in full. The lines themselves appear
        only as their first few words, but search finds a line from any word in it, accents or not, so you can type
        what you see on the page and read the English. Page numbers refer to the Vintage paperback.
      </p>

      <h2>Further reading</h2>
      <ul>
        <li>
          <a href="https://ttu-ir.tdl.org/bitstreams/ec52ab01-a89b-423d-aee5-92df180a15c4/download">
            James Luther Bell, <cite>Contextualizing Cormac McCarthy’s Border Trilogy: An Annotative Approach</cite>
          </a>
          , PhD dissertation, Texas Tech University, 2000. An annotated, place-by-place companion to the trilogy, with local research
          in the New Mexico bootheel.
        </li>
        <li>
          <a href="https://www.gaiagps.com/public/QVoNQ0FcmpOf9KOEQVRqw6l4">Joe Hazelton’s map of <cite>The Crossing</cite></a>{' '}
          on Gaia GPS, a reader’s own pins for the book’s places.
        </li>
      </ul>

      <h2>Privacy</h2>
      <p>This site doesn’t track you. It has no accounts and no cookies, and it doesn’t record how far you’ve read.</p>
      <p>
        <strong>Your place in the book</strong> is saved in your own browser, so the map opens where you left off. It
        never leaves your device.
      </p>
      {COUNTING && (
        <p>
          <strong>Visits are counted</strong> with <a href="https://www.goatcounter.com/">GoatCounter</a>, a
          privacy-friendly service. It counts which pages and map views are used, but it doesn’t keep your IP address
          and can’t tell who you are.
        </p>
      )}
      {form && (
        <p>
          <strong>Suggestions</strong> sent through{' '}
          <a href={form} target="_blank" rel="noreferrer">
            the form
          </a>{' '}
          go to <a href="https://tally.so/">Tally</a>, which runs it, and on to the site’s author. Your name and email
          are optional, and are used only to credit you in the{' '}
          <a href={`${REPO_URL}/blob/main/docs/CHANGELOG.md`}>changelog</a> and to reply. To have a suggestion deleted, ask through the same form.
        </p>
      )}
      <p>
        <strong>The details.</strong> Like any website, the services that deliver it see your IP address:{' '}
        <a href="https://pages.github.com/">GitHub Pages</a> for every page{form ? ', ' : ', and '}
        <a href="https://www.maptiler.com/">MapTiler</a> only if you switch to Satellite or Topo
        {form && ', and Tally only if you open the form'}.{' '}
        {COUNTING &&
          'GoatCounter also records the page you came from, your screen width, browser and country, and keeps its data in Finland and Germany. '}
        <a href="#/about/how-its-built">How it’s built</a> records each of these choices. Privacy policies:{' '}
        <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement">GitHub</a>,{' '}
        <a href="https://www.maptiler.com/privacy-policy/">MapTiler</a>
        {COUNTING && (
          <>
            , <a href="https://www.goatcounter.com/help/privacy">GoatCounter</a>
          </>
        )}
        {form && (
          <>
            , <a href="https://tally.so/help/privacy-policy">Tally</a>
          </>
        )}
        .
      </p>

      <h2>More</h2>
      <ul>
        <li>
          <a href="#/about/how-its-built">How it’s built</a>: the architecture, every decision record, and where the
          data comes from.
        </li>
        <li>
          <a href="#/data">The data</a>: every layer as GeoJSON and GeoParquet, free to reuse under CC BY 4.0, apart from
          the novel’s words and the translations of them.
        </li>
        <li>
          <a href="#/credits">Credits</a>: the sources of the map and their licences.
        </li>
        <li>
          <a href={REPO_URL}>The repository</a> on GitHub.
        </li>
      </ul>
    </>
  )
}
