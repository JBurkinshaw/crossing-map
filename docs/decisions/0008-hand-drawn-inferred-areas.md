# 0008. Inferred areas drawn by hand

Status: accepted (2026-11-11)
Phase: P1 (P2 for constraint models)

## Context

Many places in the book have no name: a ranch house on a volcanic plain, a camp on the road. They need an honest shape on the map.

## Decision

Draw each inferred area by hand in QGIS from the book's clues, and write the clues into the feature's `reasoning` property. A large honest area beats a precise wrong pin.

## Alternatives

Constraint modelling (travel-time rings, bearing sectors, viewsheds, slope classes) is more rigorous but slower. It is P2.

## Consequences

Fast and reviewable. Each area is a judgement call, recorded in plain words next to the geometry.
