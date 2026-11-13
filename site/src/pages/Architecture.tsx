// The system's shape (plan section 4.1), drawn in the map's ink: three places the work lives, and what
// moves between them.

type BoxProps = { x: number; y: number; w: number; h: number; title: string; lines: string[] }

function Box({ x, y, w, h, title, lines }: BoxProps) {
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} className="ink-line" />
      <rect x={x + 4} y={y + 4} width={w - 8} height={h - 8} className="ink-line thin" />
      <text x={x + w / 2} y={y + 26} textAnchor="middle" className="ink-title">
        {title}
      </text>
      {lines.map((line, i) => (
        <text key={line} x={x + 16} y={y + 50 + i * 19} className="ink-text">
          {line}
        </text>
      ))}
    </g>
  )
}

function Arrow({ x1, x2, y, label }: { x1: number; x2: number; y: number; label: string }) {
  return (
    <g>
      <line x1={x1} y1={y} x2={x2 - 8} y2={y} className="ink-line" />
      <path d={`M${x2} ${y} l-10 -5 v10 z`} className="ink-fill" />
      <text x={(x1 + x2) / 2} y={y - 7} textAnchor="middle" className="ink-text small">
        {label}
      </text>
    </g>
  )
}

export function Architecture() {
  return (
    <svg className="architecture" viewBox="0 0 860 330" role="img" aria-labelledby="architecture-title">
      <title id="architecture-title">
        A Python pipeline on the author's machine writes GeoJSON to the GitHub repository and PMTiles to a GitHub
        release; GitHub Actions validates and deploys the site to GitHub Pages; the reader's browser loads the
        story data and tiles from Pages, and satellite imagery from MapTiler only when asked.
      </title>
      <Box
        x={10}
        y={20}
        w={240}
        h={210}
        title="The author's machine"
        lines={['Python pipeline (uv)', 'gazetteers: GNIS, GeoNames,', '  Wikidata', 'Copernicus DEM, hachures', '  (QGIS), peaks, glyphs', 'tippecanoe: PMTiles', 'review CSVs, signed off']}
      />
      <Box
        x={310}
        y={20}
        w={240}
        h={210}
        title="GitHub"
        lines={['repo: data/ GeoJSON and', '  GeoParquet, schemas', 'docs/decisions/*.md', 'site/: React, Vite', 'release tiles-vN: *.pmtiles', 'Actions: validate, build,', '  deploy to Pages']}
      />
      <Box
        x={610}
        y={20}
        w={240}
        h={210}
        title="The reader's browser"
        lines={['React + MapLibre', 'story layers: GeoJSON,', '  loaded whole', 'base, relief, terrain:', '  PMTiles, range requests', 'satellite: MapTiler SDK,', '  loaded when asked']}
      />
      <Arrow x1={250} x2={310} y={95} label="git" />
      <Arrow x1={250} x2={310} y={160} label="release" />
      <Arrow x1={550} x2={610} y={125} label="HTTPS" />
      <rect x={640} y={270} width={180} height={44} className="ink-line dashed" />
      <text x={730} y={297} textAnchor="middle" className="ink-text">
        MapTiler (satellite)
      </text>
      <line x1={730} y1={270} x2={730} y2={240} className="ink-line dashed" />
      <path d="M730 230 l-5 10 h10 z" className="ink-fill" />
      <text x={130} y={262} textAnchor="middle" className="ink-text small italic">
        private: the book and caches
      </text>
      <text x={430} y={262} textAnchor="middle" className="ink-text small italic">
        public: one static site
      </text>
    </svg>
  )
}
