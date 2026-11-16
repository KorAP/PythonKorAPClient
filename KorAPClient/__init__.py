__pdoc__ = {'tests': False}

import html
import os
import re
import tempfile
import warnings
import webbrowser
from itertools import product

import pandas as pd
from rpy2.rinterface_lib.sexp import StrSexpVector, NULLType
from rpy2.robjects import numpy2ri
from rpy2.robjects.conversion import localconverter, get_conversion
from rpy2.rinterface import NULL

import rpy2.robjects as robjects
import rpy2.robjects.packages as packages
import rpy2.robjects.pandas2ri as pandas2ri
from rpy2 import rinterface as ri
from packaging import version
from rpy2.robjects.methods import RS4

CURRENT_R_PACKAGE_VERSION = "1.5.1"

KorAPClient = packages.importr('RKorAPClient')
if version.parse(KorAPClient.__version__) < version.parse(CURRENT_R_PACKAGE_VERSION):
    warnings.warn("R-package RKorAPClient version " + KorAPClient.__version__ + " is outdated, please update.",
                  DeprecationWarning)

korapclient_converter = robjects.conversion.Converter('base empty converter')

# Export NULL
NULL = NULL

@korapclient_converter.py2rpy.register(list)
def _rpy2py_robject(listObject):
    return robjects.StrVector(listObject)


@korapclient_converter.py2rpy.register(dict)
def _dict_to_named_vector(dictObject):
    """Convert dicts to named R vectors, e.g. {"Germany": "pubPlaceKey=DE"} for labelled virtual corpora."""
    if all(isinstance(value, str) for value in dictObject.values()):
        vector = robjects.StrVector(list(dictObject.values()))
        vector.names = robjects.StrVector([str(key) for key in dictObject.keys()])
        return vector
    return robjects.ListVector(dictObject)


robjects.conversion.set_conversion(robjects.default_converter + pandas2ri.converter + korapclient_converter)

fix_null_types = robjects.default_converter

@fix_null_types.rpy2py.register(NULLType)
def to_str(obj):
    return ""

fix_lists_in_dataframes = robjects.default_converter

@fix_lists_in_dataframes.rpy2py.register(StrSexpVector)
def to_str(obj):
    for i in range(len(obj)):
        obj[i] = str(obj[i])
    return "\t".join(obj)

def my_cv(obj, cv):
    if isinstance(obj, ri.StrSexpVector):
        for i in range(len(obj)):
            obj[i] = str(obj[i])
        return StrSexpVector((obj))
    else:
        return cv.rpy2py(obj)

def toDataFrame(obj):
    cv = get_conversion() # get the converter from current context
    names = []
    objects = []
    for i in range(len(obj)):
        if isinstance(obj[i], ri.ListSexpVector):
            list_name = obj.names[i] +  "." if not isinstance(obj.names, NULLType) else "l" + str(i) + "."
            for j in range(len(obj[i])):
                local_name = str(obj[i].names[j]) if not isinstance(obj[i].names, NULLType) else str(j)
                names.append(list_name + local_name)
                objects.append(obj[i][j])
        else:
            names.append(obj.names[i])
            objects.append(obj[i])


    return pd.DataFrame(
        {str(k): my_cv(objects[i], cv) for i, k in enumerate(names)}
    )

# associate the converter with R data.frame class
fix_lists_in_dataframes.rpy2py_nc_map[ri.ListSexpVector].update({"data.frame": toDataFrame})



def _call_keeping_r_result(function, *args, **kwargs):
    """Call an R function with the usual argument conversion, but return its result as unconverted R object."""
    cv = get_conversion()
    return ri.SexpClosure.__call__(function, *[cv.py2rpy(arg) for arg in args],
                                   **{key: cv.py2rpy(value) for key, value in kwargs.items()})


_flat_columns = robjects.r("""function(x)
    as.data.frame(unclass(x)[!vapply(x, is.list, logical(1))], stringsAsFactors = FALSE, check.names = FALSE)""")

_join_list_columns = robjects.r("""function(kqo) {
    join <- function(x) if (length(x) == 0 || all(is.na(x))) NA_character_ else paste(x, collapse = " ")
    df <- kqo@collectedMatches
    df[] <- lapply(df, function(column) if (is.list(column)) vapply(column, join, character(1)) else column)
    kqo@collectedMatches <- df
    kqo
}""")


def _without_na_strings(df):
    """Replace R's NA_character_ by None in the string columns of a DataFrame."""
    for name in df.columns[df.dtypes == object]:
        df[name] = df[name].map(lambda value: None if value is ri.NA_Character else value)
    return df


def _r_list_to_dict(obj):
    result = {}
    for name, value in zip(obj.names, obj):
        if isinstance(value, NULLType):
            result[name] = None
        elif isinstance(value, ri.ListSexpVector):
            result[name] = _r_list_to_dict(value)
        elif len(value) == 1:
            result[name] = None if value[0] is ri.NA_Character else value[0]
        else:
            result[name] = list(value)
    return result


def _r_value_to_py(value):
    """Convert an R scalar or vector to a Python value, with NA as None."""
    if isinstance(value, NULLType):
        return None
    values = [None if item in (ri.NA_Character, ri.NA_Integer, ri.NA_Logical) or
              (isinstance(item, float) and item != item) else item for item in value]
    return values[0] if len(values) == 1 else values


def _dispersion_to_pandas(res):
    """Convert a dispersion result with nested tables to a DataFrame with DataFrames and dicts in its list columns."""
    cv = get_conversion()
    df = _without_na_strings(_flat_columns(res))
    for position, (name, column) in enumerate(zip(res.names, res)):
        if isinstance(column, ri.ListSexpVector):
            values = [_without_na_strings(cv.rpy2py(value)) if "data.frame" in value.rclass
                      else _r_list_to_dict(value) for value in column]
            df.insert(position, name, pd.Series(values, index=df.index, dtype=object))
    return df


_hc_dispersion = robjects.r("""function(rows, distributions, apiUrls, indexRevisions, probabilities, partition, top) {
    rows <- tibble::as_tibble(rows)
    rows$distribution <- lapply(distributions, function(part) {
        part <- tibble::as_tibble(part)
        for (field in intersect(c("part", "vc", "webUIRequestUrl"), names(part)))
            part[[field]] <- as.character(part[[field]])
        part
    })
    rows$sampling <- lapply(seq_along(probabilities), function(i)
        list(apiUrl = apiUrls[[i]], indexRevision = indexRevisions[[i]], inclusionProbability = probabilities[[i]]))
    RKorAPClient::hc_dispersion(rows, partition = partition, top = top)
}""")

_save_widget = robjects.r("""function(widget, file, title)
    htmlwidgets::saveWidget(widget, file, selfcontained = FALSE, libdir = "lib", title = title)""")


def _inline_resources(document, directory):
    """Embed the scripts and stylesheets that an HTML document loads from directory into the document."""
    def read(name):
        with open(os.path.join(directory, name), encoding="utf-8") as file:
            return file.read()

    document = re.sub(r'<script src="(lib/[^"]+)"></script>',
                      lambda match: "<script>" + read(match.group(1)).replace("</script", "<\\/script") + "</script>",
                      document)
    return re.sub(r'<link href="(lib/[^"]+)" rel="stylesheet" />',
                  lambda match: "<style>" + read(match.group(1)) + "</style>", document)


class Highchart:
    """Interactive [Highcharts](https://www.highcharts.com/) chart created by an R plotting function.

    In Jupyter notebooks, the chart is displayed when it is the last expression of a cell.
    Elsewhere use `Highchart.show` or `Highchart.save`.
    """

    def __init__(self, widget, title="KorAP chart", height=600):
        self.widget = widget
        self.title = title
        self.height = height

    def to_html(self):
        """Return the chart as self-contained HTML document."""
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "chart.html")
            _save_widget(self.widget, path, self.title)
            with open(path, encoding="utf-8") as file:
                return _inline_resources(file.read(), directory)

    def save(self, path):
        """Save the chart as self-contained HTML file.

        - **path** - name of the HTML file

        Returns:
            absolute path of the HTML file
        """
        path = os.path.abspath(os.path.expanduser(path))
        with open(path, "w", encoding="utf-8") as file:
            file.write(self.to_html())
        return path

    def show(self):
        """Open the chart in the default web browser."""
        file = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
        file.close()
        webbrowser.open("file://" + self.save(file.name))

    def _repr_html_(self):
        return '<iframe srcdoc="{}" style="width: 100%; height: {}px; border: none"></iframe>'.format(
            html.escape(self.to_html(), quote=True), self.height)


def hc_dispersion(df, partition=None, top=None):
    """ **EXPERIMENTAL**: Plot the distribution of dispersion analysis results across corpus parts.

    Creates an interactive bar chart that compares, for each corpus part, its share of the corpus tokens
    with its share of the hits of each query.

    - **df** - DataFrame returned by `KorAPConnection.dispersionQuery` or `KorAPQuery.dispersionAnalysis`. Results of several calls can be combined with `pandas.concat`, as long as they refer to the same corpus parts.
    - **partition** - name of the partition to plot, e.g. `"source"`. Required if `df` contains more than one partition.
    - **top** - number of corpus parts to show individually; the remaining parts are combined (default = 12, or all parts for calendar partitions like `"year"`). Use `float("inf")` to show all parts.

    Returns:
        `Highchart`

    Details:
        The series are labelled with the `variant` column of `df` if there is one, otherwise with its `query` column.

    Example:
        ```
        $ kcon = KorAPConnection()
        $ df = kcon.dispersionQuery(["Ameisenplage", "Mückenplage"], by="region", vc="pubDate in 2022")
        $ hc_dispersion(df).save("dispersion.html")
        ```
    """
    required = ["partition", "query", "distribution", "estimated", "sampling"]
    if not isinstance(df, pd.DataFrame) or len(df) == 0 or not all(name in df.columns for name in required):
        raise ValueError("Use a result of dispersionQuery() or dispersionAnalysis() with distribution data.")
    cv = get_conversion()

    def r_list(values):
        return ri.ListSexpVector([cv.py2rpy(value) for value in values])

    def sampling_field(name, na):
        values = [sampling.get(name) if isinstance(sampling, dict) else None for sampling in df["sampling"]]
        return r_list([na if value is None else value for value in values])

    rows = df.drop(columns=["distribution", "sampling"]).reset_index(drop=True)
    widget = ri.SexpClosure.__call__(
        _hc_dispersion, cv.py2rpy(rows), r_list(df["distribution"]),
        sampling_field("apiUrl", ri.NA_Character), sampling_field("indexRevision", ri.NA_Character),
        sampling_field("inclusionProbability", ri.NA_Real),
        NULL if partition is None else cv.py2rpy(partition), NULL if top is None else cv.py2rpy(top))
    return Highchart(widget, title="Dispersion" if partition is None else "Dispersion by " + partition)


class KorAPCorpusPartition(robjects.vectors.DataFrame):
    """Corpus parts and their token counts, as returned by `KorAPConnection.corpusPartition`.

    Pass it as `partitions` argument to `KorAPConnection.dispersionQuery`. Use `toDataFrame` to inspect it.
    """

    def toDataFrame(self):
        """Returns the parts as DataFrame with columns `'part', 'value', 'vc', 'tokens'`."""
        return _without_na_strings(_flat_columns(self))


def expand_grid(dictionary):
    """Create a pandas DataFrame from all combinations of inputs

    - **dictionary** - dict with variable names as  keys and their values as vectors

    Returns:
        DataFrame with column names as specified by the dictionary key and all combinations of the specified values
        in the rows.

    Example:
        ```
        $ df = expand_grid({"Year": range(2010, 2019), "Country": ["DE", "CH"] })

        $ df["vc"] = "textType=/Zeit.*/ & pubPlaceKey = " + df.Country + " & pubDate in " + list(map(str, df.Year))
        ```
    """

    return pd.DataFrame([row for row in product(*dictionary.values())],
                        columns=dictionary.keys())


# noinspection PyPep8Naming
class KorAPConnection(RS4):
    """Connection to a KorAP server."""

    def __init__(self, *args, **kwargs):
        """Constructor keyword arguments:

        - **KorAPUrl** (default = `"https://korap.ids-mannheim.de/"`)
        - **apiVersion** (default = 'v1.0')
        - **apiUrl**
        - **accessToken** (default = `getAccessToken(KorAPUrl)`
        - **userAgent** (default = `"Python-KorAP-Client"`)
        - **timeout** - maximum time in seconds a request may take (default = 240). Long running searches are no longer
          aborted after 10 minutes of low transfer rates; only this timeout applies.
        - **verbose** (default = False)
        - **cache** (default = True)
        """
        if 'userAgent' not in kwargs:
            kwargs["userAgent"] = "Python-KorAP-Client"
        kco = KorAPClient.KorAPConnection(*args, **kwargs)
        super().__init__(kco)

    def auth(self, *args, **kwargs):
        """ Authorize PythonKorAPClient to make KorAP queries and download results on behalf of the user.

        - **kco** - `KorAPConnection` object
        - **app_id** - OAuth2 application id. Defaults to the generic KorAP client application id.
        - **app_secret** - OAuth2 application secret. Used with confidential client applications. Defaults to `NULL`.
        - **scope** - OAuth2 scope. Defaults to "search match_info".

        Returns:

            Potentially authorized `KorAPConnection`|`RS4` with access token in `.slots['accessToken']`.

        Example:
            ```
            from KorAPClient import KorAPConnection, NULL

            ### Create a KorAPConnection object without an existing access token

            kcon = KorAPConnection(accessToken=NULL, verbose=True).auth()

            ### Perform a query using the authenticated connection

            q = kcon.corpusQuery("Ameisenplage", metadataOnly=False)

            ### Fetch all results

            q = q.fetchAll()

            ### Access the collected matches

            print(q.slots['collectedMatches'].snippet)
            ```

        """

        kco = KorAPClient.auth(self, *args, **kwargs)
        super().__init__(kco)
        return self

    def corpusStats(self, *args, **kwargs):
        """Query the size of the whole corpus or a virtual corpus specified by the vc argument.

        - **vc** - virtual corpus definition, list thereof, or dict mapping labels to definitions (default = "").
          Dict keys are used as labels in a `label` column (see `KorAPConnection.frequencyQuery`).
        - **verbose** (default = kco@verbose)
        - **as.df** (default = True)
        - **cacheAs** - path to an RDS file to keep the result in (see `KorAPConnection.collocationAnalysis`)

        Returns:
            `DataFrame`|`RS4`

        Example:
            ```
            $ df = kcon.corpusStats("pubDate in 2018 & textType=/Zeit.*/ & pubPlaceKey=IT", **{"as.df": True})
            $ df["tokens"]
            12150897
            ```
        """
        default_kwargs = {"as.df": True}
        default_kwargs.update(kwargs)
        return KorAPClient.corpusStats(self, *args, **default_kwargs)

    def frequencyQuery(self, *args, **kwargs):
        """Query relative frequency of search term(s).

        - **query** - query string or list of query strings
        - **vc** - virtual corpus definition, list thereof, or dict mapping labels to definitions (default: "")
        - **conf.level** - confidence level of the returned confidence interval (default = 0.95)
        - **as.alternatives** - decides whether queries should be treated as mutually exclusive and exhaustive wrt. to some meaningful class (e.g. spelling variants of a certain word form) (default = False)
        - **KorAPUrl** - instead of specifying the `query` and `vc` string parameters, you can copy your KorAP query URL here from the browser
        - **metadataOnly** - determines whether queries should return only metadata without any snippets. This can also be useful to prevent access rewrites. (default = True)
        - **ql** - query language: `"poliqarp" | "cosmas2" | "annis" | "cql" | "fcsql"` (default = `"poliqarp"`)
        - **accessRewriteFatal** - abort if query or given vc had to be rewritten due to insufficient rights (not yet implemented) (default = `True`)
        - **verbose** - (default = `self.verbose`)
        - **expand** - bool that decides if `query` and `vc` parameters are expanded to all of their combinations (default = `len(vc) != len(query)`)
        - **cacheAs** - path to an RDS file to keep the result in (see `KorAPConnection.collocationAnalysis`)

        Returns:
            DataFrame with columns `'query', 'totalResults', 'vc', 'webUIRequestUrl', 'queryDuration', 'total', 'f',
           'conf.low', 'conf.high'`. `queryDuration` is the time in seconds a request took on the client side.
            If `vc` is a dict, its keys are used as labels in an additional `label` column.
            A warning is issued if a request failed or the server cut a search short (`timeExceeded`).

        Example:
            ```
            $ kcon = KorAPConnection(verbose=True)
            $ kcon.frequencyQuery("Ameisenplage", vc=["pubDate in "+str(y) for y in range(2010,2015)])
                                  query  totalResults  ...      conf.low     conf.high
            1  Ameisenplage             3  ...  9.727696e-10  1.200289e-08
            2  Ameisenplage            12  ...  3.838218e-09  1.275717e-08
            3  Ameisenplage             5  ...  2.013352e-09  1.356500e-08
            4  Ameisenplage             6  ...  2.691331e-09  1.519888e-08
            5  Ameisenplage             3  ...  8.629463e-10  1.064780e-08
            ```

            To label virtual corpora, pass a dict:
            ```
            $ vc = {"Germany": "pubPlaceKey=DE", "Switzerland": "pubPlaceKey=CH"}
            $ kcon.frequencyQuery("Ameisenplage", vc=vc)[["query", "label", "totalResults"]]
                      query        label  totalResults
            1  Ameisenplage      Germany           178
            2  Ameisenplage  Switzerland            27
            ```
        """
        return KorAPClient.frequencyQuery(self, *args, **kwargs)

    def collocationScoreQuery(self, node, collocate, vc="", **kwargs):
        """Get collocation scores for given node(s) and collocate(s).

        - **node** - target word
        - **collocate** - collocate of target word or list thereof (all combinations of collocates and vcs are queried)
        - **vc** - virtual corpus definition, list thereof, or dict mapping labels to definitions (default: ""). Dict keys are used as labels.
        - **lemmatizeNodeQuery** - logical, set to TRUE if node query should be lemmatized, i.e. x -> [tt/l=x]
        - **lemmatizeCollocateQuery** - logical, set to TRUE if collocate query should be lemmatized, i.e. x -> [tt/l=x]
        - **leftContextSize** - size of the left context window
        - **rightContextSize** - size of the right context window
        - **scoreFunctions** - dict of R (!) score functions of the form function(O1, O2, O, N, E, window_size), see e.g. KorAPClient.pmi
        - **smoothingConstant** - smoothing constant will be added to all observed values
        - **cacheAs** - path to an RDS file to keep the result in (see `KorAPConnection.collocationAnalysis`)

        Returns:
            DataFrame with columns `'node', 'collocate', 'label', 'vc','webUIRequestUrl', 'w',  'leftContextSize',
               'rightContextSize', 'N', 'O', 'O1', 'O2', 'E', 'pmi', 'mi2', 'mi3', 'logDice', 'll'`

        Example:
            ```
            $ kcon = KorAPConnection(verbose=True)
            $ df = kcon.collocationScoreQuery("Grund", "triftiger")
            ```
        """
        return KorAPClient.collocationScoreQuery(self, node, collocate, vc, **kwargs)

    def collocationAnalysis(self, node, vc="", **kwargs):
        """ **EXPERIMENTAL**: Performs a collocation analysis for the given node (or query) in the given virtual corpus.

        - **node** - target word or list of target words
        - **vc** - string, list of strings, or dict mapping labels to strings describing the virtual corpus in which the query should be performed. An empty string (default) means the whole corpus, as far as it is license-wise accessible.
        - **lemmatizeNodeQuery** - if True, node query will be lemmatized, i.e. x -> [tt/l=x]
        - **minOccur** - minimum absolute number of observed co-occurrences to consider a collocate candidate
        - **leftContextSize** - size of the left context window
        - **rightContextSize** - size of the right context window
        - **topCollocatesLimit** - limit analysis to the n most frequent collocates in the search hits sample
        - **searchHitsSampleLimit** - limit the size of the search hits sample
        - **ignoreCollocateCase** - bool, set to True if collocate case should be ignored
        - **withinSpan** - KorAP span specification (see <https://korap.ids-mannheim.de/doc/ql/poliqarp-plus?embedded=true#spans>) for collocations to be searched within. Defaults to `base/s=s`
        - **exactFrequencies** - if False, extrapolate observed co-occurrence frequencies from frequencies in search hits sample, otherwise retrieve exact co-occurrence frequencies
        - **stopwords** - vector of stopwords not to be considered as collocates
        - **seed** - seed for random page collecting order
        - **expand** - if True, node and vc parameters are expanded to all of their combinations
        - **minObservedExpectedRatio** - minimum ratio of observed to expected co-occurrence frequency for a collocate
          to be kept (default = 1, i.e. collocates occurring less often than expected by chance are discarded). Set to 0
          for the unfiltered results of earlier versions.
        - **cacheAs** - path to an RDS file to keep the result in. If the file exists and records the same call, it is
          read back instead of contacting the server; otherwise the analysis is run and its result stored there
          (`.rds` is appended if missing). By default, no file is used.

        Returns:
            DataFrame with columns `'node', 'collocate', 'label', 'vc','webUIRequestUrl', 'w',  'leftContextSize',
               'rightContextSize', 'N', 'O', 'O1', 'O2', 'E', 'pmi', 'mi2', 'mi3', 'logDice', 'll'`

        Details:
            The collocation analysis is currently implemented on the client side, as some of the functionality is not yet provided by the KorAP backend. Mainly for this reason it is very slow (several minutes, up to hours), but on the other hand very flexible. You can, for example, perform the analysis in arbitrary virtual corpora, use complex node queries, and look for expression-internal collocates using the focus function (see examples and demo).
            `logDice` is computed as defined by Rychlý (2008), `14 + log2(2 * O / (O1 + O2))`, so that values are comparable to those of other tools. `ll` follows Evert (2004).
            When `vc` is a list or dict of virtual corpora, the results are compared across them (**experimental**, see `?collocationAnalysis` in R).
            To increase speed at the cost of accuracy and possible false negatives, you can decrease searchHitsSampleLimit and/or topCollocatesLimit and/or set exactFrequencies to FALSE.
            Note that currently not the tokenization provided by the backend, i.e. the corpus itself, is used, but a tinkered one. This can also lead to false negatives and to frequencies that differ from corresponding ones acquired via the web user interface.

        Example:
            ```
            $ kcon = KorAPConnection(verbose=True)
            $ df = kcon.collocationAnalysis("Grund")
            ```
        """
        return KorAPClient.collocationAnalysis(self, node, vc, **kwargs)

    def mergeDuplicateCollocates(self, *args, **kwargs):
        """Merge collocation analysis results for different context positions."""
        return KorAPClient.mergeDuplicateCollocates(*args, **kwargs)


    def corpusQuery(self, *args, **kwargs):
        """Query search term(s).

        - **query** - query string or list of query strings
        - **vc** - virtual corpus definition or list thereof (default: "")
        - **KorAPUrl** - instead of specifying the `query` and `vc` string parameters, you can copy your KorAP query URL here from the browser
        - **metadataOnly** - determines whether queries should return only metadata without any snippets. This can also be useful to prevent access rewrites. (default = True)
        - **ql** - query language: `"poliqarp" | "cosmas2" | "annis" | "cql" | "fcsql"` (default = `"poliqarp"`)
        - **fields** - (meta)data fields that will be fetched for every match (default = `["corpusSigle", "textSigle", "pubDate",  "pubPlace", "availability", "textClass", "dmozDomain", "wikiDomain", "snippet", "tokens"]`).
          Since DeReKo-KorAP-2026-II, the topic domain of DeReKo texts is given by `dmozDomain` and `wikiDomain` instead of `textClass`.
        - **verbose** - (default = `self.verbose`)

        Returns:
            `KorAPQuery`

        Example:
            ```
            $ kcon = KorAPConnection(verbose=True)
            $ q = kcon.corpusQuery("Ameisenplage")
            $ q = q.fetchAll()
            $ q.slots['collectedMatches']
                corpusSigle  ...                                          textClass
            1         WPD17  ...                                                NaN
            2         WPD17  ...                                                NaN
            3         WPD17  ...                                                NaN
            4         WPD17  ...                                                NaN
            5         WPD17  ...                                                NaN
            ..          ...  ...                                                ...
            126         Z83  ...                       freizeit-unterhaltung reisen
            127       MZE03  ...  freizeit-unterhaltung reisen natur-umwelt wett...
            128       MZE03  ...  freizeit-unterhaltung reisen staat-gesellschaf...
            129       MZE14  ...  wissenschaft populaerwissenschaft freizeit-unt...
            130       MZE00  ...                  wissenschaft populaerwissenschaft
            [130 rows x 6 columns]
            ```
        """
        return KorAPQuery(self, *args, **kwargs)
    
    def textMetadata(self, textSigle, **kwargs):
        """ Retrieves metadata for a text, identified by its sigle (id) using the corresponding KorAP API
        (see `Kustvakt Wiki https://github.com/KorAP/Kustvakt/wiki/Service:-Metadata-Retrieval`).

        - **textSigle** - unique text id (concatenation of corpus, document and text ids, separated by `/`, e.g. ) or list thereof
        - **cacheAs** - path to an RDS file to keep the result in (see `KorAPConnection.collocationAnalysis`)

        Returns:
            DataFrame with columns for each metadata property. In case of errors, such as non-existing texts/sigles, the tibble will also contain a column called `errors`.
            If there are metadata columns you cannot make sense of, please ignore them. The function simply returns all the metadata it gets from the server.

        Example:
            ```
            $ kcon = KorAPConnection(verbose=True)
            $ kcon.textMetadata(["WUD17/A97/08542", "WUD17/B96/57558", "WUD17/A97/08541"])
            ```
        """
        return KorAPClient.textMetadata(self, textSigle, **kwargs)

    def maintenanceInfo(self, refresh=False):
        """Inspect planned maintenance of the KorAP instance

        Retrieves the public maintenance schedule from the KorAP frontend of the connected instance. No authorization is needed.
        Before server requests, the client checks for maintenance notices at most once every five minutes and announces each
        maintenance window. To disable these checks, run `rpy2.robjects.r("options(rkorap.maintenance.notices = FALSE)")`.

        - **refresh** - if True, bypass the five-minute schedule cache (default = `False`)

        Returns:
            dict with `'state'` (`"ok"`, `"stale"`, `"unknown"` or `"unsupported"`), `'time_zone'`, the Unix timestamps
            `'last_success'` and `'valid_until'` and an `'events'` DataFrame with the columns `'start', 'end'` (ISO 8601),
            `'start_epoch', 'end_epoch'` (Unix timestamps), `'all_day'` and `'ongoing'`. All-day end dates are exclusive.
            An empty schedule with state `"unknown"` does not mean that no maintenance is planned.

        Example:
            ```
            $ kcon = KorAPConnection()
            $ kcon.maintenanceInfo()["events"]
            ```
        """
        res = _call_keeping_r_result(KorAPClient.maintenanceInfo, self, refresh=refresh)
        cv = get_conversion()
        return {name: cv.rpy2py(value) if "data.frame" in value.rclass else _r_value_to_py(value)
                for name, value in zip(res.names, res)}

    def corpusPartition(self, by="source", values=None, vc="", **kwargs):
        """ **EXPERIMENTAL**: Define corpus parts for a dispersion analysis.

        Discovers metadata groups and their token counts, or defines a custom partition. Discovery checks the base
        corpus independently of query hits, so that parts without hits are retained.

        - **by** - metadata field. The aliases `"source"`, `"year"` and `"region"` stand for `corpusTitle`, `pubDate` (publication year) and `pubPlaceKey` respectively.
        - **values** - list of metadata values, or dict mapping part labels to values. If neither `values` nor `parts` is given, the groups are discovered automatically.
        - **vc** - base virtual corpus. All parts are intersected with this corpus. (default = "")
        - **parts** - alternatively, a dict mapping part labels to virtual corpus definitions
        - **regex** - optional trailing-suffix grouping rule for automatic discovery (see `KorAPQuery.dispersionAnalysis`)
        - **verbose** - (default = `self.verbose`)
        - **cacheAs** - path to an RDS file to keep the result in (see `KorAPConnection.collocationAnalysis`)

        Returns:
            `KorAPCorpusPartition` that can be passed to `KorAPConnection.dispersionQuery`.
            Use its `toDataFrame()` method to get the parts with their virtual corpus definitions and token counts.
            A warning is issued if the listed parts do not cover the whole base corpus.

        Example:
            ```
            $ kcon = KorAPConnection()
            $ countries = kcon.corpusPartition("region", ["DE", "AT", "CH"], vc="pubDate in 2022")
            $ countries.toDataFrame()[["part", "tokens"]]
              part       tokens
            1   DE  681374138.0
            2   AT  121466921.0
            3   CH   96168291.0
            $ kcon.dispersionQuery("Ameisenplage", partitions=countries)
            ```
        """
        if isinstance(values, dict):
            kwargs["values"] = {label: str(value) for label, value in values.items()}
        elif values is not None:
            kwargs["values"] = [str(value) for value in values]
        return KorAPCorpusPartition(_call_keeping_r_result(KorAPClient.corpusPartition, self, by, vc=vc, **kwargs))

    def dispersionQuery(self, query, partitions=None, **kwargs):
        """ **EXPERIMENTAL**: Query the dispersion of search term(s) across corpus metadata.

        Computes dispersion measures for one or more queries, i.e. how evenly their hits are distributed across
        corpus parts such as sources, countries or years, taking the sizes of the parts into account.

        - **query** - query string or list of query strings
        - **partitions** - `KorAPCorpusPartition` (see `KorAPConnection.corpusPartition`) or dict of them. If not given, the groups are discovered automatically using `by`.
        - **by** - metadata field or list of fields for automatic grouping: `"source"` (default), `"year"`, `"region"` or a metadata field name
        - **regex** - optional trailing-suffix grouping rule for automatic grouping (see `KorAPQuery.dispersionAnalysis`)
        - **vc** - base virtual corpus for automatic grouping (default = ""). With explicit partitions, their base virtual corpus is used instead.
        - **scoreFunctions** - dict of R (!) measure functions of the form function(frequencies, sizes), see e.g. `KorAPClient.dispersionDP`. (default = `KorAPClient.defaultDispersionFunctions()`)
        - **exactFrequencies** - if True (default), request exact counts for each part. If False, estimate them from a sample of at most `searchHitsSampleLimit` hits.
        - **searchHitsSampleLimit** - maximum metadata sample size (default = 20000)
        - **seed** - seed for the random selection of result pages (default = 7)
        - **ql** - query language (default = `"poliqarp"`)
        - **verbose** - (default = `self.verbose`)
        - **cacheAs** - path to an RDS file to keep the result in (see `KorAPConnection.collocationAnalysis`)

        Returns:
            DataFrame with one row per query and partition and the columns `'query', 'partition', 'totalResults',
            'sampledHits', 'usedHits', 'excludedHits', 'nParts', 'estimated', 'rangeIsLowerBound', 'distribution',
            'sampling'`, followed by one column per measure, by default `'DP', 'DPnorm', 'JuillandD', 'CarrollD2',
            'RosengrenS', 'range'`. Each `distribution` cell holds a DataFrame with the sizes, hit counts, relative
            frequencies and concordance URLs of the corpus parts; each `sampling` cell holds a dict that records how
            the counts were obtained.

        Details:
            Smaller `DP` and `DPnorm` values mean a more even distribution, whereas larger `JuillandD`, `CarrollD2` and `RosengrenS` values do. `range` is the number of parts with at least one hit.
            Discovering the groups of a metadata field and their sizes can take time on the first call, especially for `by="source"` in large virtual corpora.
            See `?dispersionQuery` and `` ?`dispersion-score-functions` `` in R for the interpretation of the measures.

        Example:
            ```
            $ kcon = KorAPConnection()
            $ df = kcon.dispersionQuery(["Ameisenplage", "Mückenplage"], by="region", vc="pubDate in 2022")
            $ df[["query", "totalResults", "nParts", "DP", "JuillandD", "range"]]
                      query  totalResults  nParts        DP  JuillandD  range
            1  Ameisenplage           2.0       7  0.265146   0.000000    1.0
            2   Mückenplage          18.0       7  0.062939   0.495076    3.0
            $ df["distribution"].iloc[1][["part", "tokens", "frequency"]]
            ```
        """
        if partitions is not None:
            kwargs["partitions"] = partitions
        return _dispersion_to_pandas(_call_keeping_r_result(KorAPClient.dispersionQuery, self, query, **kwargs))

class KorAPQuery(RS4):
    """Query to a KorAP server."""

    def __init__(self, *args, **kwargs):
        kco = KorAPClient.corpusQuery(*args, **kwargs)
        super().__init__(kco)

    def fetchNext(self, *args, **kwargs):
        """Fetch next couple of query results

        - **offset** - start offset for query results to fetch
        - **maxFetch** - maximum number of query results to fetch
        - **verbose**
        - **randomizePageOrder** - fetch result pages in pseudo random order if true. (default = `False`)

        Returns:
            `KorAPQuery`
        """

        res = KorAPClient.fetchNext(self, *args, **kwargs)
        with localconverter(fix_lists_in_dataframes):
            df = res.slots['collectedMatches']
        res.slots['collectedMatches'] = df
        super().__init__(res)
        return self

    def fetchRest(self, *args, **kwargs):
        """Fetch remaining query results

        - **verbose**

        Returns:
            `KorAPQuery`
        """
        res = KorAPClient.fetchRest(self, *args, **kwargs)
        with localconverter(fix_lists_in_dataframes):
            df = res.slots['collectedMatches']
        res.slots['collectedMatches'] = df
        super().__init__(res)
        return self

    def fetchAll(self, *args, **kwargs):
        """Fetch all query results

        - **verbose**

        Returns:
            `KorAPQuery`

        Example:
            See `KorAPConnection.corpusQuery`.
        """
        res = KorAPClient.fetchRest(self, *args, **kwargs)
        with localconverter(fix_lists_in_dataframes):
            df = res.slots['collectedMatches']
        res.slots['collectedMatches'] = df
        super().__init__(res)
        return self

    def fetchAnnotations(self, *args, **kwargs):
            """Fetches and parses linguistic annotations for the collected matches.

            This method enriches the `collectedMatches` DataFrame with additional columns
            containing linguistic annotations like lemma, part-of-speech (POS), and
            morphology for each token in the match and its context.

            Args:
                foundry (str, optional): The foundry (annotation layer) to fetch.
                                        Defaults to "tt" (TreeTagger).
                overwrite (bool, optional): If True, existing annotation columns will be
                                            overwritten. Defaults to False.
                verbose (bool, optional): If True, prints progress information. Defaults
                                        to the verbosity setting of the
                                        KorAPConnection object.
                *args: Positional arguments passed to the underlying R function.
                **kwargs: Keyword arguments passed to the underlying R function.

            Returns:
                KorAPQuery: A new KorAPQuery object with the `collectedMatches` DataFrame
                            updated to include the fetched annotations.

            Example:
                ```
                from KorAPClient import KorAPConnection

                # Authentication might be required for snippets and annotations
                kcon = KorAPConnection(verbose=True).auth()

                # Perform a query and fetch all matches
                q = kcon.corpusQuery("Ameisenplage", metadataOnly=False).fetchAll()

                # Fetch annotations for the matches
                q_annotated = q.fetchAnnotations()

                # Display the collected matches with new annotation columns
                print(q_annotated.slots['collectedMatches'][['snippet', 'lemma.left', 'lemma.match', 'lemma.right']].head())
                ```
            """
            res = KorAPClient.fetchAnnotations(self, *args, **kwargs)
            with localconverter(fix_lists_in_dataframes):
                df = res.slots['collectedMatches']
            res.slots['collectedMatches'] = df
            super().__init__(res)
            return self

    def fetchSamplePages(self, *args, **kwargs):
        """Fetch a reproducible random sample of result pages

        Unlike `fetchNext`, which takes the first hits, complete result pages are selected at random from the
        entire result set. If all results fit within the limit, all of them are fetched.

        - **maxHits** - maximum number of hits to retrieve. Complete pages are used, so the limit is rounded down to a multiple of 50. (default = 2000)
        - **seed** - seed for choosing pages (default = 7)
        - **verbose**
        - **warn** - warn that the result is a sample of pages (default = True)

        Returns:
            `KorAPQuery`, whose sample is reused by `KorAPQuery.dispersionAnalysis`

        Example:
            ```
            $ q = KorAPConnection().corpusQuery("Gendern").fetchSamplePages(maxHits=2000, seed=7)
            $ q.dispersionAnalysis(by="region")
            ```
        """
        # multivalued metadata fields, such as dmozDomain, are joined by spaces, as in the other fetch methods
        res = _join_list_columns(KorAPClient.fetchSamplePages(self, *args, **kwargs))
        super().__init__(res)
        return self

    def dispersionAnalysis(self, by="source", **kwargs):
        """ **EXPERIMENTAL**: Calculates how evenly the hits of the query are distributed across corpus metadata.

        The groups of the chosen metadata dimension and their sizes are discovered automatically, including
        groups without hits.

        - **by** - metadata field or list of fields. `"source"` (default) groups by `corpusTitle`, ignoring trailing years; `"year"` groups `pubDate` by publication year; `"region"` uses `pubPlaceKey`.
        - **regex** - optional regular expression removing a trailing suffix from metadata values, ending in `$`, e.g. `" [0-9]{4}$"`, which is the default for `by="source"`
        - **scoreFunctions** - dict of R (!) measure functions (see `KorAPConnection.dispersionQuery`)
        - **exactFrequencies** - by default, a sample fetched with `KorAPQuery.fetchSamplePages` or completely fetched metadata are reused; otherwise exact counts per group are requested. True requests exact counts even after a fetch; False permits sampling metadata.
        - **searchHitsSampleLimit** - maximum metadata sample size (default = 20000)
        - **seed** - seed for the random selection of result pages (default = 7)
        - **verbose**
        - **cacheAs** - path to an RDS file to keep the result in (see `KorAPConnection.collocationAnalysis`)

        Returns:
            DataFrame as described in `KorAPConnection.dispersionQuery`

        Details:
            Use a metadata-only query, which is the default of `KorAPConnection.corpusQuery`.
            To compare the dispersion of several queries, use `KorAPConnection.dispersionQuery`.

        Example:
            ```
            $ q = KorAPConnection().corpusQuery("Mückenplage", vc="pubDate in 2022")
            $ df = q.dispersionAnalysis(by="region")
            $ df[["query", "partition", "totalResults", "nParts", "DP", "DPnorm", "range"]]
                     query partition  totalResults  nParts        DP    DPnorm  range
            1  Mückenplage    region          18.0       7  0.062939  0.062939    3.0
            ```
        """
        return _dispersion_to_pandas(_call_keeping_r_result(KorAPClient.dispersionAnalysis, self, by, **kwargs))
