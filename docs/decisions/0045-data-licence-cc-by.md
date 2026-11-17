# 0045. The data and notes stay under CC BY 4.0

Status: accepted (2026-11-16)
Phase: P1

## Context

The data and notes in `data/` were CC BY 4.0, marked provisional until launch. Several sources ask for credit (GeoNames, GMBA, the CEC land cover, GRanD), INEGI's terms ask for "Fuente: INEGI" and a note of changes, and the Copernicus DEM licence binds everyone downstream of a derived product. [`licensing.md`](../licensing.md) sets out the reading behind this decision.

## Decision

- The data and notes are CC BY 4.0, except where a feature's `source_licence` says otherwise.
- `data/LICENSE` also says that the layers derived from the Copernicus DEM are subject to its licence, and that the quotations from *The Crossing* are not licensed.

## Alternatives

- **CC0.** It would drop the credits GeoNames, GMBA, the CEC and GRanD require.
- **CC BY-SA 4.0.** Allowed with these sources, and it keeps adapted versions open. But it stops the data going into CC0 projects such as Wikidata, or into OpenStreetMap.
- **ODbL.** Share-alike like BY-SA, and meant for databases. It brings the same limits and suits no source here.

## Consequences

- Anyone can reuse the data with credit, including in closed or commercial work.
- The Copernicus-derived layers carry an extra obligation, so a reuser has to read `data/README.md` for them as well as the CC BY licence.
- No ODbL or share-alike data can enter `data/` without changing this decision.
