import { REPO_URL } from './format'

export function About() {
  return (
    <>
      {/* The working blurb from the plan (section 1). */}
      <p className="lede">
        I read <cite>All the Pretty Horses</cite> years ago, and only recently got to <cite>The Crossing</cite>. It left
        me wanting to know the country its characters travel through, and the geographer in me needed to see these
        places more closely. <cite>The Crossing</cite> moves through real
        country: the Animas Valley, the Peloncillos, the Bavispe, the Babícora. This is a map of where Billy, Boyd,
        “the girl” and the she-wolf went, built from real geographic data and marked honestly where the book leaves
        us guessing.
      </p>

      <h2>How to read it</h2>
      <p>
        Every place, stop, route and area on the map says how sure it is, and where it came from. There are four
        levels of certainty:
      </p>
      <dl className="terms">
        <dt>Located</dt>
        <dd>A gazetteer has the very place the book names.</dd>
        <dt>Approximate</dt>
        <dd>The pin stands in for something larger, such as a range by its high point.</dd>
        <dt>Inferred</dt>
        <dd>The book gives no name; the place is worked out from clues in the text, and the reasoning is written down.</dd>
        <dt>Reported</dt>
        <dd>A character says it happened there, and the book gives us no more than that.</dd>
      </dl>
      <p>
        Routes follow a road or river where the text names one, and are drawn as gentle curves where it does not.
        Inferred areas are drawn no smaller than the evidence allows: a large honest area is better than a precise
        wrong pin.
      </p>

      <h2>What is here and what is not</h2>
      <p>
        The notes are our own words. The site does not reproduce the novel’s text. Page numbers refer to the Vintage edition.
      </p>

      <h2>More</h2>
      <ul>
        <li>
          <a href="#/about/how-its-built">How it’s built</a>: the architecture, every decision record, and where the
          data comes from.
        </li>
        <li>
          <a href="#/data">The data</a>: every layer as GeoJSON and GeoParquet, free to reuse under CC BY 4.0.
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
