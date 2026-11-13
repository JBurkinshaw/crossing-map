"""Draw the PLACEHOLDER vignette SVGs and rebuild the map sprite (plan section 10).

Run from the repo root: uv run --project pipeline python art/vignettes/make_vignettes.py
Needs spreet (cargo install spreet).

These are not the vignettes. Each is a plain silhouette in the map's ink and paper, inside a dashed frame
that marks it as provisional, on the plan's 96 x 96 grid, so that the anchors, sizes and collisions can be
judged on the map. The real drawings will be the owner's or an illustrator's (plan section 10, and Phase 2
for more by an illustrator); each replaces the file of the same name in svg/, named vignette-<id> as in
pipeline/seeds/vignettes.csv.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_sprite import build_sprite  # noqa: E402  (art/build_sprite.py, shared with the mountain glyphs)

SVG_DIR = Path(__file__).parent / "svg"
INK, PAPER = "#2b2118", "#e4ddcc"

# Each silhouette as SVG shapes on the 96 x 96 grid: filled with paper and stroked in ink at 1.5 px.
SHAPES = {
    "she-wolf": [
        '<path d="M18,50 C26,41 50,39 64,42 L70,36 L76,29 L78,22 L82,30 L90,35 L88,40 L78,42 L74,48 L72,62 L75,74 L70,74'
        ' L66,60 L58,56 L44,56 L36,60 L34,74 L29,74 L30,60 L26,55 C20,58 14,62 9,67 C11,60 14,54 18,50 Z"/>',
    ],
    "steel-trap": [
        '<circle cx="38" cy="40" r="16"/>',
        '<rect x="32" y="34" width="12" height="12"/>',
        '<path d="M54,40 L84,35 L84,45 Z"/>',
        '<path d="M22,40 L8,36 L8,44 Z"/>',
        '<path d="M40,56 L46,62 L52,68 L58,74 L64,80" fill="none" stroke-dasharray="4 2"/>',
        '<path d="M64,80 L72,86 M72,86 Q82,84 84,74 M72,86 Q76,93 88,90" fill="none"/>',
    ],
    "obelisk": [
        '<path d="M42,22 L48,10 L54,22 L57,78 L39,78 Z"/>',
        '<rect x="33" y="78" width="30" height="7"/>',
        '<path d="M12,86 L84,86" fill="none"/>',
        '<path d="M52,30 L55,32 M53,42 L56,44 M53,54 L56,56 M54,66 L57,68" fill="none" stroke-width="0.8"/>',
    ],
    "hacienda-pit": [
        '<path d="M14,60 L14,30 L26,30 L26,38 Q48,12 70,38 L70,30 L82,30 L82,60 L70,60 L70,44 Q48,24 26,44 L26,60 Z"/>',
        '<path d="M12,30 L28,30 M68,30 L84,30" fill="none"/>',
        '<ellipse cx="48" cy="80" rx="30" ry="9"/>',
        '<path d="M22,78 L22,70 M34,74 L34,66 M48,72 L48,64 M62,74 L62,66 M74,78 L74,70" fill="none"/>',
    ],
    "ruined-church": [
        '<path d="M18,86 L18,42 L32,42 L32,30 L42,24 L48,12 L54,24 L62,30 L62,42 L72,42 L76,54 L70,60 L78,68 L76,86 Z"/>',
        '<path d="M40,86 L40,68 Q48,58 56,68 L56,86" fill="none"/>',
        '<path d="M45,34 L45,28 Q48,24 51,28 L51,34 Z" fill="none"/>',
        '<path d="M8,86 L88,86" fill="none"/>',
    ],
    "paquime": [
        '<path d="M8,84 L8,58 L24,58 L24,44 L50,44 L50,32 L72,32 L72,50 L88,50 L88,84 Z"/>',
        '<path d="M30,84 L30,72 L26,72 L26,64 L42,64 L42,72 L38,72 L38,84" fill="none"/>',
        '<path d="M58,56 L58,48 L54,48 L54,42 L66,42 L66,48 L62,48 L62,56" fill="none"/>',
        '<path d="M4,84 L92,84" fill="none"/>',
    ],
    "san-diego-gate": [
        '<path d="M18,86 L18,40 Q48,4 78,40 L78,86 L66,86 L66,48 Q48,26 30,48 L30,86 Z"/>',
        '<path d="M14,40 L82,40" fill="none"/>',
        '<path d="M38,50 L38,60 L44,60 M50,50 L58,50 M54,50 L54,60" fill="none" stroke-width="1.2"/>',
        '<path d="M8,86 L88,86" fill="none"/>',
    ],
    "opera-caravan": [
        '<path d="M14,64 L14,38 Q44,22 74,38 L74,64 Z"/>',
        '<path d="M20,52 Q28,44 36,52 T52,52 T68,52" fill="none" stroke-width="0.8"/>',
        '<circle cx="28" cy="72" r="10"/>',
        '<circle cx="62" cy="72" r="10"/>',
        '<path d="M74,60 L90,54" fill="none"/>',
    ],
    "blind-man": [
        '<circle cx="44" cy="18" r="7"/>',
        '<path d="M36,12 L52,12" fill="none"/>',
        '<path d="M44,25 L55,31 L53,62 L33,62 L36,31 Z"/>',
        '<path d="M38,62 L34,86 M48,62 L50,86" fill="none"/>',
        '<path d="M53,36 L62,48 M62,48 L70,88" fill="none"/>',
    ],
    "red-plane": [
        '<rect x="8" y="34" width="80" height="12" rx="3"/>',
        '<ellipse cx="48" cy="52" rx="6" ry="32"/>',
        '<rect x="34" y="76" width="28" height="7" rx="2"/>',
        '<path d="M38,22 L58,22 M24,34 L24,46 M72,34 L72,46" fill="none"/>',
    ],
    "gypsy-plane": [
        '<rect x="10" y="64" width="76" height="8"/>',
        '<circle cx="22" cy="80" r="7"/>',
        '<circle cx="74" cy="80" r="7"/>',
        '<path d="M12,62 L78,52 L88,40 L86,60 Z"/>',
        '<path d="M30,40 L60,40 L64,58 L26,58 Z" fill="none"/>',
        '<path d="M36,40 L35,58 M43,40 L43,58 M50,40 L51,58 M56,40 L58,58" fill="none" stroke-width="0.8"/>',
    ],
    "crippled-dog": [
        # Hindquarters dropped and one hind leg drawn up; the head tilted.
        '<path d="M12,70 C16,58 34,50 52,48 L62,44 L68,40 L70,32 L75,38 L86,40 L84,47 L74,52 L70,58 L72,78 L67,78 L63,62'
        ' L50,62 L36,68 L30,80 L25,80 L27,72 L20,74 L14,72 Z"/>',
    ],
    "trinity-cloud": [
        # A mushroom cloud: the cap, the stem rising from a skirt of dust, the desert floor.
        '<path d="M24,40 C14,40 12,28 22,24 C22,14 34,8 42,14 C46,6 60,8 62,16 C72,12 84,20 78,30 C86,34 82,44 72,42'
        ' C64,48 34,48 24,40 Z"/>',
        '<path d="M42,46 C44,58 42,70 36,80 L60,80 C54,70 52,58 54,46 Z"/>',
        '<path d="M16,84 C20,76 32,76 38,80 C44,74 54,74 60,80 C66,76 78,76 82,84 Z"/>',
        '<path d="M6,86 L90,86" fill="none"/>',
    ],
}


def svg(shapes: list[str]) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96">'
        # The dashed frame says "placeholder" on the map; a real drawing has none.
        f'<rect x="1" y="1" width="94" height="94" rx="6" fill="none" stroke="{INK}" stroke-opacity="0.5" stroke-dasharray="5 4"/>'
        f'<g fill="{PAPER}" stroke="{INK}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
        f'{"".join(shapes)}</g></svg>'
    )


def main() -> None:
    SVG_DIR.mkdir(exist_ok=True)
    for old in SVG_DIR.glob("*.svg"):
        old.unlink()
    for name, shapes in SHAPES.items():
        (SVG_DIR / f"vignette-{name}.svg").write_text(svg(shapes))
    print(f"{len(SHAPES)} placeholder vignettes")
    build_sprite()


if __name__ == "__main__":
    main()
