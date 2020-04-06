# companies
Gather company 10K filings from the SEC for the banking industry using Selenium. Process them using Beautiful Soup and Regular Expressions. Save them to a MongoDB database.

## Get Data from the SEC
  - Use Python Selenium package to get the 10K forms.
  - Save them to the file system

## Clean data
  - Two file types were found - text and HTML/XML
  - Extract all tables in the 10K filing using Regular Expressions and save to the file system
  - TODO: Convert each HTML/XML table into JSON with row/col headers and value of the cell
  - TODO: Convert each text table into JSON with row/col headers and value of the cell
  
## Load data into the database
  - TODO: Use MongoDB to save JSON for each file
