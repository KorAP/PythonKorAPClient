# Version history

## 1.5.1

- Updates recommended RKorAPClient version to 1.5.1
- Added **experimental metadata-based dispersion analysis**, to compare how evenly hits are distributed across sources, countries, years or other metadata, accounting for the sizes of the corpus parts:
  - `KorAPQuery.dispersionAnalysis()` calculates dispersion measures (DP, DPnorm, Juilland's D, Carroll's D2, Rosengren's S, range) for a query
  - `KorAPConnection.dispersionQuery()` does the same for one or more query strings, optionally across custom corpus parts
  - `KorAPConnection.corpusPartition()` defines or discovers corpus parts and their token counts
  - `KorAPQuery.fetchSamplePages()` fetches a reproducible random sample of result pages, which `dispersionAnalysis()` reuses
  - the results are DataFrames whose `distribution` column holds the per-part counts as DataFrames
  - `hc_dispersion()` plots the shares of the corpus parts as interactive chart (`Highchart`), which is displayed in Jupyter notebooks and can be saved as HTML file with `save()` or opened in the browser with `show()`
- retrieval handles server rate limits and failed page downloads more reliably, with warnings for incomplete results
- `KorAPConnection.maintenanceInfo()` shows planned and ongoing maintenance of the KorAP instance; maintenance notices are also announced before server requests
- an expired stored access token no longer breaks the connection: `KorAPConnection()` warns and continues without authorization
- the local cache of API responses is kept across minor releases and when the access token is renewed

## 1.4.1

- Updates recommended RKorAPClient version to 1.4.1
- Requires Python >= 3.10 (support for Python 3.7–3.9 dropped, Python 3.14 added)
- `libv8` is no longer needed as a system dependency
- Python dicts are now converted to named R vectors (or named lists), e.g. `vc={"Germany": "pubPlaceKey=DE", "Switzerland": "pubPlaceKey=CH"}` to label virtual corpora
- Documentation and tests updated for the new features listed below, including labelling virtual corpora (`label` column) and caching results with `cacheAs`
- follows the DeReKo-KorAP-2026-II release: `corpusQuery()` now fetches the new `dmozDomain` and `wikiDomain` metadata fields, which replaced `textClass` ([RKorAPClient #31](https://github.com/KorAP/RKorAPClient/issues/31))
- long running searches are no longer aborted after 10 minutes; only the connection's `timeout` applies
- `corpusQuery()` and `frequencyQuery()` now warn about failed or incomplete (`timeExceeded`) searches instead of silently reporting 0 or too few hits; their results carry a new `queryDuration` column
- clearer verbose output: series of queries or virtual corpora are logged as an aligned table, with more accurate ETAs
- `cacheAs` parameter for transparent result caching, now supported by `collocationAnalysis()`, `frequencyQuery()`, `corpusStats()`, `collocationScoreQuery()` and `textMetadata()`
- names of a named `vc` vector are consistently used as labels by `frequencyQuery()`, `corpusStats()` and `collocationScoreQuery()`
- **changed `logDice` values**: now computed as defined by Rychlý (2008), so values are comparable to Sketch Engine and other tools
- **changed `ll()` values**: contingency table now scales the sample size and both marginals with the window size (Evert 2004)
- `collocationAnalysis()` discards collocates occurring less often than expected by chance (new `minObservedExpectedRatio` parameter, default 1; set to 0 for the previous behaviour)
- *experimental* support for comparing collocation analyses across multiple (optionally labelled) vcs
- `collocationScoreQuery()` accepts a vector of collocates
- fixed collocation analysis dropping snippets with certain markup shapes, e.g. sentence-bounded `contains(<base/s=s>, ...)` queries ([RKorAPClient #14](https://github.com/KorAP/RKorAPClient/issues/14))
- fixed score threshold in recursive collocation analysis

## 1.2.1

- Updates recommended RKorAPClient version to 1.2.1
- fetchAnnotations() method added to KorAPQuery class, to fetch annotations for all collected matches

## 1.1.0

- Updates recommended RKorAPClient version to 1.1.0
- fixed bug with fetching result pages with an offset >= 10,000 (=1e+05 ...) [issue #25](https://github.com/KorAP/RKorAPClient/issues)
- timed out corpus queries are no longer cached (see [issue #7](https://github.com/KorAP/RKorAPClient/issues/7))
- improved stability of `ci` function
- improved error handling
- improved logging
- added ETAs to logging in verboose mode

## 1.0.1

- Fixed NULL warning in fetch functions

## 1.0.0

- Simplified authorization process for accessing restricted data via the new `auth()` function
- Fixed issues with tokenized matches in `corpusQuery` results
- Fixed smoothing constant in `mergeDuplicateCollocates` function
- Fixed chainability of fetch methods in `corpusQuery`

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
