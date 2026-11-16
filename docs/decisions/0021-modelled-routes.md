# 0021. Least-cost routes for the sierra and valley legs

Status: accepted (2026-11-14); J7 leg 41 traced on the Río Casas Grandes instead, by 0032
Phase: P1

## Context

Most legs in Mexico are schematic curves, because the book names no road or river for them. Across a sierra or up a long valley a curve crosses the ground blind and reads as a diagram, not a ride. An experiment (`review/experiments/least-cost/`, cost model lc-0.3) routed 86 legs as least-cost paths and found the model useful on the sierra and valley legs and of no use on the flat ones. The owner adopted it on 14 November 2026 for the legs on its "works" list.

## Decision

- **Which legs.** The 21 legs in `pipeline/seeds/modeled-legs.csv`: the sierra and canyon legs (J1 1 and 2, the wolf; J2 6 to 8 and 12; J3 12; J4 13 to 15; J7 23, 24, 36 and 37) and the long valley legs (J4 20; J5 2 and 11; J7 26; J7 41 to 43). Flat legs and summary legs (weeks of riding told as turning points) stay curves. Reported legs and legs by car, bus or train are never modelled.
- **The model, lc-0.4.** `crossing.least_cost` routes each leg on a 90 m grid (coarser for legs over about 100 km) in a local transverse Mercator projection, with scipy's Dijkstra over eight neighbours. Speed is Tobler's hiking function scaled to 6 km/h on the flat for a horse at a walk (unscaled for the wolf). Steep ground (over 30 %), canyon walls (side slope over 25 %, except on canyon floors), river fords (0.5 to 4 minutes by Strahler order, INEGI 1:50,000) and lakes cost more; the wolf avoids towns; a rider in Mexico crosses the border only at the book's gates. Where the seed names a road, cells within 1 km of INEGI's unpaved tracks and footpaths (Red Nacional de Caminos) or Natural Earth's railroads cost 20 % less; for a river trail, cells within 300 m of the river do. lc-0.4 differs from the experiment's lc-0.3 only in the road corridor: INEGI's tracks replace Natural Earth's modern highways.
- **Drawing.** Each path is simplified (Douglas-Peucker at 150 m, then one round of Chaikin's corner cutting) and published as `method: modeled`, `certainty: inferred`, with `cost_model` and a reasoning text that begins "A modelled path, not the book's". The map draws it in long dashes, between the solid narrated paths and the short-dashed curves, with its own key entry.
- **The story wins.** J4 legs 19 and 20 keep the stops the text gives, although the model makes the day's ride about 100 km and some 16 hours at a walk. The leg's note and the open question `q-j4-one-day-ride` say so.
- **Cached.** Each result is cached under `private/cache/least-cost/routes/`, keyed by the stop points, the leg's settings and the model version, so a rebuild reruns only the legs whose stops moved.

## Alternatives

- **A band instead of a line** (the spread between the full model and slope alone), to carry the doubt. More honest, heavier on a crowded map; the owner chose a line with its own style.
- **Modelling every leg.** On flat ground the model returns the curve with wiggles, which suggests a precision the book does not have.
- **Period roads** from the Army Map Service 1:250,000 sheets or the USGS historical topographic maps, which would make the road legs better than today's tracks. Left for later (roadmap).

## Consequences

The sierra legs read as rides over the ground. The weights are assumptions: on about 11 legs a run on slope alone moves the line by 5 km or more. A change to a modelled leg's stop reruns that leg (a few seconds each). The build needs INEGI's tracks in `private/cache/roads/inegi/`, and fails with the path if they are missing.
