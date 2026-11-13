# Stage 7 review: second sources

Five agents compared every place in Bell's index of *The Crossing* (Bell 2000; 172 entries, plus 9 the scan had merged into neighbours), all 135 of Joe Hazelton's Gaia waypoints, Bell's map of Hidalgo County and his chronology and character index, against our data, the text and the gazetteers. The findings are in `private/sources/stage7/` (they quote Bell, so they stay private).

**Result:** 215 findings, as follows.

- **Confirmed:** 153, of which 124 are high confidence.
- **High-confidence changes:** 9, already made (commit 08e0890, "Correct Part I places against Bell and Hazelton"):
  - the Pilares Teras moved onto the range inside the Bavispe's bend
  - Skeleton Creek moved onto its south fork
  - four new places: Hidalgo County, Cochise County, Taylor's Draw and Cañón la Cabellera
  - `first_seen` corrected for the Animas Peaks (1-01) and Ascensión (1-09)
  - real reasoning in place of placeholders for Black Point, Hog Canyon Spring and the hacienda
- **Small factual fixes:** made in commit 46075f4.
- **Judgement calls:** the 17 numbered items below, worked through one at a time, with a recommendation for each. Item 14 alone covers 13 street-level places.

**Bell's map of Hidalgo County (Figure 3.2)**, georeferenced on ten towns to about 0.8 km RMS, confirms our Cloverdale, San Luis Pass, Black Point, Guadalupe Mountains and Hermanas, each within about 2 km.

**Where Hazelton's pins and ours disagree** by more than 10 km, ours stands after checking:

| Place | Hazelton's pin | Distance |
| --- | --- | --- |
| Álamo | an Álamo in Sonora | 211 km |
| Las Ramadas | a hill named Cerro las Ramadas | 121 km |
| La Boquilla | a La Boquilla near Mata Ortiz | 102 km |
| Peloncillo Mountains | the range near Lordsburg | 79 km |
| Fort Bliss | the training range | 107 km |
| Santa Rita | the Tyrone mine | 33 km |
| Sierra del Nido | a village of that name | not measured |

## A. Where a place or stop sits

1. **Sierra de la Madera (J1's first stop).** Our pin is GeoNames 9028461, the Sky Island range near Cumpas and Huásabas. It is cited to a USDA paper and lies west of the Bavispe's southward reach, so the wolf's crossing of the river comes naturally. Bell describes, and Hazelton pins, the other Sierra de la Madera (GeoNames 3996948), east of the upper Bavispe near Bacerac, 81 km from ours and 116 km from the border crossing. From there the wolf would cross the Bavispe westwards, which is the wrong way for a wolf heading north-east to the line. **Recommendation:** keep ours, and say on the card that Bell and Hazelton read it as the eastern range.

2. **Casas Grandes: the old town or the new?** Our point is old Casas Grandes, beside the Paquimé ruins. But the brothers ride into town over the railroad tracks and past the depot (2-08), and Billy crosses the railroad embankment to Alameda Street (3-09). The only station is at Nuevo Casas Grandes, 5 km north-east, and Hazelton puts Alameda Street and the Camino Recto Hotel there. The ruins belong to the old town; the depot and the town scenes fit the new one. **Recommendation:** keep the place on the old town for the ruins, and move the five town-scene stops (J4 twice, J5, J7 twice) to Nuevo Casas Grandes, with reasoning that cites the depot.

3. **The Parham house, north of Cloverdale.** Our house sits on the Cloverdale point. In 1-08 Billy leaves before light, rides south along the road and reaches Cloverdale at first grey light, so the house is a few kilometres north of the settlement. Bell reads it the same way. Moving the house moves the SK Bar estimate too (nine miles from the house), and Bell's "Robertson's crossfence" lies about 5 km west of our circle for it. **Recommendation:** move the house to an inferred circle 3-6 km north of Cloverdale on the Cloverdale road, and shift the SK Bar estimate with it.

4. **Cloverdale Creek: the trap and the creek road.** Both J1's trap stop and J2's creek-road stop fall back to the GNIS point for the creek, which is its mouth south-east of Cloverdale. In the text Billy turns up the creek road from Cloverdale, westwards, and rides about two hours to the trap. Bell, the NHD line and TIGER's Cloverdale Road all run north-west from the town. **Recommendation:** move both stops to an inferred circle about 7 km north-west of Cloverdale, up the creek (radius 5 km).

5. **Cajón Bonito (J2).** Our stop is GeoNames' point at the stream's lower end, 47 km from Cloverdale and 29 km west of Billy's line south. He reaches the canyon a few hours after crossing the border, then follows it south. Hazelton's pin on the upper canyon, 27 km south of Cloverdale, fits the text. **Recommendation:** move the stop to an inferred circle on the upper canyon. The place point can stay on the GeoNames feature.

6. **Between Clanton and Foster draws (J1).** The area is centred on the two GNIS points, which are the draws' mouths on the valley floor. The text keeps the wolf up in the high ground between the draws, coming down to the plains at night. Our Foster Draw stop is also at the mouth, while the calf is found at its head. **Recommendation:** move the area about 7 km west onto the draws' middle reaches, and the Foster Draw stop to the draw's head (GNIS gives both ends).

7. **Starvation Canyon (J1).** Our point is the canyon's mouth. The wolf goes to where the canyon heads, then south to Hog Canyon Spring. The head, also from GNIS, is 6.4 km south-east, and 2.4 km north of the spring, which fits that order. **Recommendation:** move to the head.

8. **De Baca County's first mention.** Billy names it in 1-08, saying where the family came from before Grant County; we have 4-07. Decision 0010 uses this county as an example of a later first mention, so changing it means correcting that example too. **Recommendation:** change it to 1-08 and fix the example.

## B. Places to add from local evidence

9. **The old Nations road (J1).** The wolf crosses it about a mile into New Mexico after the line at 108°30′ W. Bell's informant took it for the road to the Nations homestead, and GNIS has a Nations Tank 1.4 km north of the border beside Whitewater Creek. **Recommendation:** add an inferred stop between the crossing and the creek, credited to Bell.

10. **Fitzpatrick Wells.** The text names only the old road to the wells, which Billy and his father cross. Bell ties the wells to the Fitzpatrick ranch about 4 miles east-south-east of Cloverdale. TIGER's Fitzpatrick Camp Road ends there, and Hazelton's pin is 20 m from that road end. **Recommendation:** add it as an approximate place at the road end, credited to Bell and Hazelton.

11. **Pendleton's ranch.** Billy meets three vaqueros from Pendleton's. Only Bell's informant places the ranch, about 5 miles north-west of Cloverdale, and Hazelton's approximate pin agrees. No gazetteer has it. **Recommendation:** add it as an inferred area, credited to Bell, at low certainty.

12. **Ciénega Springs and Government Draw.** An old rancher remembers driving cattle up the valley from Ciénega Springs and camping the first night in Government Draw (1-08). GNIS has a Cienega Springs at the south end of the Animas Valley, and a Government Tank 21 km north of it, but no Government Draw. Bell's informant puts the springs elsewhere, about 16 km north-east of Cloverdale. **Recommendation:** leave both unmapped. They are a memory in a story told to Billy, and the two sources disagree.

13. **Don Arnulfo's house.** Billy rides to consult him at his house on the plain south of Animas (1-07). We map no Part I side trips beyond the two journeys. This is a question of scope, not evidence. **Recommendation:** leave it unmapped for now, and revisit it in the declutter pass.

## C. Street-level places

14. **Streets and buildings.** Bell's research gives real addresses for scenes in town. Each would be a small point inside its town, visible from zoom 14, with the map's maximum zoom raised from 13 to 15.

| Town | Places | Stops |
| --- | --- | --- |
| Deming | the bus station at Spruce and Gold; the armory at 301 South Silver, now the museum; the Manhattan Cafe at 123 South Gold; Dr Moir's office at 421 West Pine | J7 |
| Silver City | the Palace Hotel at 106 West Broadway; the feed store on Bullard Street | J7 |
| El Paso | the recruiting office on San Antonio Street; the Splendid Cafe on South El Paso Street | J7 |
| Casas Grandes | Alameda Street; the Camino Recto Hotel (both depend on item 2) | J4, J7 |
| Caborca | the old mission church (a tale place) | none |

TIGER on disk places the Deming and Silver City streets. The rest need lookups: TIGER for El Paso County, INEGI's street network for Mexico, and an address or Sanborn sheet for exact buildings. That is roughly ten network requests. **Recommendation:** add them all, with the lookups, as child points of their towns.

## D. Smaller items

15. **Veracruz.** Gaspar, the drunk gypsy, comes from Veracruz, and the text doesn't say whether it means the city or the state. **Recommendation:** add it to "Named elsewhere" as the state, as Bell reads it.

16. **Bell's local history as notes.** About 20 short notes, paraphrased and cited by page, would add context to existing places and stops:
    - Cloverdale's store, post office and school dates
    - Clanton Draw's name, from the Tombstone Clantons
    - the Hashknife outfit's history
    - Grant County's strip south to the railroad
    - the Echols homestead and the Diamond A range
    - the Ash Wednesday date that does not fit the book's own calendar
    - and others

    Each would need a check for spoilers at its feature's `first_seen`. **Recommendation:** add them, as a batch reviewed together.

17. **Overrides now backed by a second source.** Hazelton's pins agree to within 0.6 km for Divisaderos, Flores Magón, Ignacio Zaragoza and La Norteña, and Bell's distances agree for Guzmán. **Recommendation:** raise these from medium to high confidence and cite the agreement.
