# Bundled grow-light fixtures

Each JSON filename, without `.json`, is the fixture ID. In a fixture's PPFD
table, rows correspond to canopy distances and columns correspond to output
percentages. See the [manager README](../../../../README.md#manage-the-catalogs)
for import commands.

## BloomStar FLUXshield Habibi 150

The [fixture profile](bloomstar-fluxshield-habibi-150.json) uses PPFD averages
for a 40 × 40 cm footprint from revision 1.2 of the manufacturer's datasheet.
[Crescience datasheet](https://resources.cre.science/Datasheets/Bloomstar/fluxshield_habibi_150-de.pdf#page=3)

The API interpolates between measured output and distance values. Beyond the
published grid, results can be `extrapolated` or `unavailable`.

To estimate a single light level, call
`GET /api/grow-lights/bloomstar-fluxshield-habibi-150/ppfd?output_percent=35&canopy_distance_cm=25`.
The starter profile returns 250 µmol/m²/s with status `interpolated`.
