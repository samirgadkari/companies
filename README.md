# companies
Web scrape company 10K filings from the SEC for the banking industry using Selenium. Extract tables from each filing using Beautiful Soup and Regular Expressions. Save them on the local filesystem. Convert the HTML tables to JSON so we can easily access the data. Main goal is to segment companies and gain more knowledge about each segment.

## Get Data from the SEC
  - Use Python Selenium package to get the 10K filings.
  - Save them to the file system

## Extract data
  - Two file types were found - text and HTML/XML
  - Extract all tables in the 10K filing (using Beautiful Soup and Regular Expressions), and save to the file system
  - TODO: Convert each HTML/XML table into JSON with row/col headers and value of the cell
    - One attempt was made to programmatically extract data. The tables were in HTML format, but there were many variations. This attempt was not successful.
    - Second attempt:
      - Convert HTML text to PDF using pdfkit
      - Convert PDF to PNG using pdf2image
      - Use pytesseract (Python API on Google's Tesseract OCR system) to convert PNG to bounding boxes in pixels
      - Programmatically try to combine the correct bounding boxes into table title, row headers, column headers, and cell values
      This attempt was also not successful - there will still too many variations. The table title couldbe positioned to the top-left, or the top middle part of the page, The number of columns varied. The number of rows in each column heading would vary from table to table, etc.
    - Third attempt:
      - Covert using Machine Learning (since doing it programmatically is difficult). This means some of our tables will have erroneous converted values, but at least some will work.
        - Converted some HTML tables manually to JSON. Since it is tedious to do this, wrote code to replace row/column headings and cell values to random strings. Then these initial set of tables can result in a larger set of varied tables. The good part of this is that the neural network does not fixate on the values of the headings/cells. It should just look at the positional mapping between the HTML and JSON files.
        - Tried to do this in Tensorflow 2, but could not get the preprocessing correct.
        - Learning how to do the preprocessing in Pytorch now.
  
## TODO: Load JSON into the MongoDB database
## TODO: Write code to segment the companies
  - Maybe using t-SNE as it creates larger gaps between clusters
  - But maybe we need to precede that with a PCA dimension reduction. This will make t-SNE run faster. Not sure if this is really needed.
