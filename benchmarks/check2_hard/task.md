You are given destination_performance.csv, brief.txt, and a list of candidate
web-image URLs in image_candidates.txt.

Create a polished Excel artifact at:

final/visual_brief.xlsx

Also create a verification report next to the artifact at:

final/README.txt

The workbook must:
- contain the source data and useful summary analysis;
- contain a required "Scenario & Sensitivity" sheet with at least three
  what-if scenarios: a 15% load-factor change, a marketing-mix reallocation,
  and a refund-rate reduction;
- calculate every scenario result with Excel formulas that reference clearly
  labeled assumption cells and workbook data (not hard-coded scenario outputs),
  and show the baseline, scenario result, and delta for at least one
  management-relevant KPI per scenario;
- contain at least three meaningful charts derived from the data, including a
  bar-and-line combination chart and a stacked bar chart showing seasonality;
- place the charts on dedicated chart-only worksheets, separate from the
  source-data, scenario, and executive-brief worksheets;
- include at least two relevant images obtained from the web-image URLs;
- when fetching web images, retry with backoff on transient HTTP errors
  (429/5xx) until each needed image is downloaded;
- include the chosen images inside the workbook, not only as hyperlinks;
- attach each chosen image to the relevant worksheet with openpyxl (e.g.
  `ws.add_image(Image(path), anchor)`) so it is a real worksheet image, not
  only a file inside the workbook zip;
- place a visible figure caption in worksheet cells next to each embedded
  image;
- contain a Sources sheet listing, for every included image, its source URL,
  figure caption, and attribution;
- contain an "Executive Brief" sheet with at least five quantified insights;
- state the relevant value(s) and explicitly cite the exact workbook data
  range or ranges used for every Executive Brief insight (for example,
  `Source Data!$D$2:$D$145`);
- use the available `bin/vision-helper` when visual inspection of an image is
  needed;
- make the charts/images materially relevant rather than decorative.

Before finishing, reload the saved workbook with openpyxl and verify that it
opens successfully. Count the charts, worksheet images, and source URLs in the
reloaded workbook, and write the actual numbers into final/README.txt using
clearly labeled `Charts:`, `Images:`, and `Source URLs:` lines. The README must
also state whether each required minimum passed.

Do not create any other final deliverable.


CRITICAL: You MUST actually write the final workbook file to disk at final/visual_brief.xlsx
using a Python script you run (e.g. openpyxl save), then reload it and write
final/README.txt. Do not finish without creating both files.


NOTE: This is a text-only coding model. You must NOT attach or send images to the
model API. For any visual inspection of downloaded images, use the `bin/vision-helper`
tool (e.g. `bin/vision-helper --file path/to/image.jpg --question "what city is this?"`).
Embedding images into the workbook is done with openpyxl directly from local files.
