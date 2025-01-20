# Version history

## 0.9.0

- Updates recommended RKorAPClient version to 0.9.0
- Added `matchStart` and `matchEnd` columns to corpusQuery results, containing the start and end positions of the match in the text
- Added `mergeDuplicateCollocates` function to merge collocation analysis results for different context positions
- Added a query column to collocation analysis results
- Improved documentation for span parameter in `collocationAnalysis` functions
- Updated `textMetadata` method to use new metadata fields API, if available, to retrieve custom metadata for a text based on its sigle
- Added new unit tests to cover the new features and changes

## 0.8.1

- Updates recommended RKorAPClient version to 0.8.1
- fixed rare frequencyQuery incompatibility with outdated KorAP instances (see KorAP/Kustvakt#668)

## 0.8.0

- Updates recommended RKorAPClient version to 0.8.0
- Added `textMetadata` KorAPConnection method to retrieve all metadata for a text based on its sigle
- Added `webUiRequestUrl` column also to corpusStats results, so that also virtual corpus definitions can be linked to / tested directly in the KorAP UI
- Uses server side tokenized matches in collocation analysis, if supported by KorAP server
- Unless `metadataOnly` is set, also tokenized snippets are now retrieved in corpus queries 
  (stored in `res.slots['collectedMatches']['tokens.left']`, `res.slots['collectedMatches']['tokens.match']`, 
   `res.slots['collectedMatches']['tokens.right']`). Because Pandas data frames cannot store lists, tokens are stored as strings, tab separated.

- Python 3.11 and 3.12 are now supported
- Python 3.7 support has been dropped (by rpy2 dependency)

## 0.7.5

- Updates recommended RKorAPClient version to 0.7.5
  - fixes collocation scores for lemmatized node or collocate queries
- Automatically converts again between rpy and py objects, most importantly between Pandas and R data frames, also with newer versions of [rpy2](https://github.com/rpy2)
  - Fixes "Hello world" example in Readme.md
- Updates references / citation information
- Changes corpusStats to return a pandas.DataFrame by default
- Advertises Python 3.10 as supported
- Adds interactive plot examples using [Vega-Altair](https://altair-viz.github.io/)

## 0.7.1
