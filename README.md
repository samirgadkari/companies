# companies
Predict company performance for all companies in the banking industry from past company 10K SEC filings.

## Get Data from the SEC
  - Use Python requests package to get the excel spreadsheets.
  - Upload them to a PostgreSQL database (ElephantDB).

## Clean data
  - Download data from the database.
  - Extract names of all cell identifiers (based on the first column text values of each of the Balance Sheet, Income Statement, Cash Flow statement).
  - Find unique tags from the tags list above
  - Combine tags into groups. Many times the same element is referred to in multiple different ways.
  - Extract only the groups you need
  - Convert values to actual numbers (such statements give "all values are in thousands/millions/billions" at the top)
  - Save cleaned data to database
  - Apply:
    - Time series models (in Python)
    - Ridge Regression/Lasso (in Python)
    - Random Forest/XDG regressors (in Python)
    - Neural Networks (Tensorflow) (in Python)
  
 ## Explore data (in R)
  - Load cleaned data from database
  - Explore data to find the best set of features
  - Select and apply:
    - Time series models
