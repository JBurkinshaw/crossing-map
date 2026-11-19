# Rivers: INEGI's centre lines (13 November 2026)

**The defect.** INEGI's Red Hidrográfica stores the channel of a wide river as `ENTIDAD = 'LINEA CENTRAL'`, not `'CORRIENTE DE AGUA'`. `tiles/mexico_rivers.py` reads only `'CORRIENTE DE AGUA'`, so `tiles-v6` loses the main stems of the largest rivers (about 16,600 segments of Strahler order 3 and up, about 2,900 of them order 7 or 8). Where they are missing, the traced river jumps along gap joins or falls back to Natural Earth's line. The areas experiment found it near Colonia Morelos.

**The test.** The same build with `WHERE ENTIDAD IN ('CORRIENTE DE AGUA', 'LINEA CENTRAL')`, nothing else changed. In a box around Colonia Morelos (109.45 to 109.05 W, 30.6 to 31.1 N), the share of the traced rivers that lies on INEGI lines rises from 52% to 88%. `morelos.png` shows the two side by side. One straight run remains near 30.83 N, where the network still breaks.

**Rolling it out.** A one-line change in `tiles/mexico_rivers.py`, then `tiles/build_base.py`, a new `base.pmtiles`, and a `tiles-v7` release (owner). The same filter is in `crossing.plan_oblique` (the Raised view's rivers) and in the new `crossing.least_cost`; both would take the same change, and the Raised archives would need rebuilding.
