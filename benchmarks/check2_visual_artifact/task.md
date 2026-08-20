You are given destination_performance.csv, brief.txt, and a list of candidate
web-image URLs in image_candidates.txt.

Create a polished Excel artifact at:

final/visual_brief.xlsx

The workbook must:
- contain the source data and useful summary analysis;
- contain at least two meaningful charts derived from the data;
- include at least two relevant images obtained from the web-image URLs;
- when fetching web images, retry with backoff on transient HTTP errors (429/5xx) until each needed image is downloaded;
- include the chosen images inside the workbook, not only as hyperlinks;
- attach each chosen image to the relevant worksheet with openpyxl (e.g. `ws.add_image(Image(path), anchor)`) so it is a real worksheet image, not only a file inside the workbook zip;
- contain a Sources sheet listing the source URL for each included web image;
- use the available `bin/vision-helper` when visual inspection of an image is
  needed;
- make the charts/images materially relevant rather than decorative.

Before finishing, verify that the workbook opens successfully and that the
requested charts, images, and source URLs are present.

Do not create any other final deliverable.


CRITICAL: You MUST actually write the final workbook file to disk at final/visual_brief.xlsx
using a Python script you run (e.g. openpyxl save). Do not finish without creating that file.
