# Experiment: can Billy see the Carretas Plain from the eastern escarpment? (J3 stop 5)

Status: **tried 18 November 2026.** The owner chose option 1: the stop stays, and the open question `q-eastern-escarpment` shows the view as the other reading (decision 0059).

## The question

In episode 2-01 Billy reaches the eastern escarpment of the Sierras, sits on a rim of grey rock and looks east over the broad barranca of the Bavispe to the Carretas Plain beyond it. He sees a locomotive's smoke on the plain about forty miles off. Then he goes down to the river and rides north along it to a ford, where he finds Huisiachepic.

The stop (`j3-eastern-escarpment`) was placed from the order of events, not from the view. Huisiachepic is an estimate on the upper Bavispe, and the escarpment was put south-west of it, because he rides north to the ford. Its area is the ground west of the river, within 8 km of it, that drops 300 m or more within 6 km to the east. Nothing in either tested the view. This experiment does.

## In short

- **From almost nowhere on the escarpment can he see the Carretas Plain.** 617 lookouts every 1.5 km along the escarpment west of the Bavispe, from 29.8 N to 30.9 N, were tested with a viewshed. 4 see 1 km² or more of it. The ranges east of the river stand higher than the escarpment and hide the plain.
- **The stop's own stretch sees none.** No lookout between 29.8 N and 30.1 N sees any part of the plains east of the sierras, of Carretas or anywhere else. The stop is at 29.99 N.
- **The two lookouts that see it well are west of Bavispe town,** at about 30.66 N, 109.15 W, on ground at 2,300 to 2,400 m. One sees 92 km² of the plain, its nearest part 56 km away. That is close to the book's forty miles (64 km). They are 16 km from stop 2's point (the promontory over the Bavispe), and 75 km north-west of Huisiachepic.
- **The flats around the old Hacienda Carretas** (70 km² within 15 km of it, east of the river) are seen from none of the lookouts either.
- **The locomotive cannot be tested.** No railway in the data runs on the Carretas Plain. Natural Earth's line through Casas Grandes and Mata Ortiz is out of sight of every lookout, and more than 100 km off.

So the clues disagree. The order of events (go down, ride north along the river to the ford) puts the escarpment south of Huisiachepic. The view puts it about 75 km further north, west of Bavispe town, where riding north along the river would not reach Huisiachepic as the map places it. Either the view is not literal, or the escarpment, Huisiachepic, or both are further north than the map has them.

## Options for the owner

1. **Keep the stop where it is and record the conflict** in a new open question ("Where on the escarpment?"), showing the order-of-events reading, with the view as the other reading. This is my recommendation: the order of events is the stronger clue for a route, and a novelist's view east over "the Carretas Plain" may name the country beyond rather than ground in sight.
2. **Move the stop north to the lookouts that see the plain.** This needs Huisiachepic, and perhaps Tamichopa's order, revisited, since he rides north to the ford afterwards.
3. **Widen the area** to cover both readings. It would cover 80 km of the sierra and say little.

## Method

`pipeline/src/crossing/escarpment_view.py`:

1. **Ground.** The Copernicus GLO-30 DEM warped to a transverse Mercator grid (WGS 84, centred at 30.3 N, 108.6 W) at 90 m, averaged. It is bare earth, with no trees or buildings.
2. **The river.** INEGI's 1:50,000 streams of Strahler order 7 and up that are joined to the stream nearest Huisiachepic's pin. Pieces up to 3 km apart count as joined, because the lines break between map sheets just north of Bacerac.
3. **The escarpment.** Cells west of the river, within 15 km of it, whose ground drops 300 m or more within 6 km to the east. This is the stop's area rule, widened from 8 km to 15 km.
4. **Lookouts.** The highest escarpment cell in each 1.5 km square, 617 in all. The eye is 1.7 m above the ground.
5. **The plains.** Ground flatter than 2 degrees, on the DEM smoothed over 270 m, that is joined to GeoNames' point for the Llanos de Carretas (4015316). GeoNames rounds that point to the half degree (31.0 N, 108.5 W). The plains form one piece of 9,649 km² that runs south to Casas Grandes. The Carretas Plain is the part within 35 km of the GeoNames point or of the old Hacienda Carretas (GeoNames 4015318), 2,874 km².
6. **Viewsheds.** `gdal_viewshed`, with the earth's curvature and refraction (coefficient 0.13, GDAL's default). The target is the ground. For the railway the target is smoke 50 m above the track, east of the lookout.

**Limits.** The 90 m grid smooths small rims that could open a view. Trees are ignored, and they would only block more. The plain's extent depends on the 2 degree threshold and the 35 km radius. The test is whether any part of the plain is in sight, which is generous.

## Files

- `pipeline/src/crossing/escarpment_view.py`. Run it with `uv run --project pipeline python -m crossing.escarpment_view` (about 3 minutes, with the viewsheds cached in `private/cache/escarpment-view/`). Add `--with matplotlib ... --figure` for the figure.
- `results.csv`: the 55 lookouts with the biggest drop in each 2 km band, what each sees (river, plains, the Carretas Plain, the railway), and its distance from the stop and from Huisiachepic.
- `bands.csv`: per 0.1 degree of latitude, the lookouts tested and how many see the Carretas Plain.
- `observers.geojson`: every lookout, with what it sees, and the Carretas Plain's outline.
- `img/escarpment-view.png` (not in git): the lookouts on a hillshade, green where they see the plain.
