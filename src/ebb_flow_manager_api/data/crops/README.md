# Bundled crop profiles

Each JSON filename, without `.json`, is the crop ID. Each profile groups its
growth phases under `phases`. The [Lettuce profile](lettuce.json) shows the
supported target fields and units. See the
[manager README](../../../../README.md#manage-the-catalogs) for import commands.

## Lettuce

In the [Lettuce profile](lettuce.json), seedling pH, air temperature, and light
use Cornell's post-germination settings. Cornell specifies a seedling EC of
1.2 mS/cm above the source water. The catalog shows
1.2 mS/cm as the measured target for low-EC source water. The seedling reservoir
temperature and humidity use conditions reported in separate lettuce seedling
trials. Lettuce production PPFD approximates 17 mol/m²/day over 16 hours of
constant light. Lettuce production EC uses the Oklahoma State extension table.
[Cornell lettuce handbook](https://cea.cals.cornell.edu/files/2019/06/Cornell-CEA-Lettuce-Handbook-.pdf) ·
[Lettuce seedling reservoir trial](https://www.nature.com/articles/s41598-026-52581-w) ·
[Lettuce seedling humidity trial](https://www.mdpi.com/1424-8220/24/13/4225) ·
[Oklahoma State pH and EC guide](https://extension.okstate.edu/fact-sheets/electrical-conductivity-and-ph-guide-for-hydroponics)

## Basil

In the [Basil profile](basil.json), seedling pH and EC apply once the seed leaves
have expanded. Seedling air temperature and light use the Iowa State propagation
trial, and humidity uses a separate sweet basil propagation trial. Both phases use the reservoir
temperature range from the Iowa State production trial as a starting point.
Basil production air temperature and humidity span the night and day setpoints
of an ebb-and-flow trial. Production pH, EC, and DLI use the extension tables.
Seedling DLI and production PPFD assume 16 hours of constant light.
[Basil propagation guide](https://hortamericas.com/wp-content/uploads/2015/11/Hort-Americas-fertilizer-product-info-112015.pdf) ·
[Iowa State basil trial](https://journals.ashs.org/downloadpdf/view/journals/horttech/25/5/article-p645.pdf) ·
[Basil propagation humidity trial](https://doi.org/10.1111/1750-3841.70224) ·
[Basil ebb-and-flow trial](https://www.frontiersin.org/journals/agronomy/articles/10.3389/fagro.2026.1866628/full) ·
[Oklahoma State pH and EC guide](https://extension.okstate.edu/fact-sheets/electrical-conductivity-and-ph-guide-for-hydroponics) ·
[Virginia Tech DLI guide](https://www.pubs.ext.vt.edu/content/pubs_ext_vt_edu/en/SPES/spes-720/spes-720.html)

## Kohlrabi

The [Kohlrabi profile](kohlrabi.json) draws on an ebb-and-flow microgreen
trial for its seedling targets. Production pH and EC draw on a purple kohlrabi
coir trial that found its best yield at 1.31 mS/cm. A separate coir trial
estimated an optimum of 1.96 mS/cm
for stem weight. The daytime temperature and humidity use FAO's stem-formation
guidance.
[Colorado State trial](https://mountainscholar.org/items/584a338d-db41-46ed-9f3b-8295e8b24f9b) ·
[Purple kohlrabi trial](https://www.scielo.br/j/rbeaa/a/gyJ7sbKqyr883hyNGdP4XJd/?lang=en) ·
[Coir EC trial](https://www.scielo.br/j/hb/a/Ggv5j4q6hNb7VnCfyQCq74B/) ·
[FAO greenhouse guide, chapter 8](https://iris.unito.it/retrieve/e27ce42b-89e9-2581-e053-d805fe0acbaa/2017_FAO%20GAP%20for%20greenhouse%20vegetable%20production%20in%20SEE%20countries.pdf)

Kohlrabi reservoir temperatures use general hydroponic leafy-green guidance.
Production PPFD uses mature Chinese kale as a reference. Both Kohlrabi DLI
ranges assume 16 hours of constant light at the corresponding canopy PPFD.
[Root-zone guidance](https://bpb-us-w2.wpmucdn.com/u.osu.edu/dist/e/50423/files/2020/03/Root-Zone-Management-Handout-2019.pdf) ·
[Chinese kale lighting trial](https://pmc.ncbi.nlm.nih.gov/articles/PMC9695120/)
