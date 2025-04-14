__pdoc__ = {'tests': False}

import warnings
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

CURRENT_R_PACKAGE_VERSION = "1.0.0"

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
        - **timeout** (default = 110)
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

        - **vc** (default = "")
        - **verbose** (default = kco@verbose)
        - **as.df** (default = True)

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
        - **vc** - virtual corpus definition or list thereof  (default: "")
        - **conf.level** - confidence level of the returned confidence interval (default = 0.95)
        - **as.alternatives** - decides whether queries should be treated as mutually exclusive and exhaustive wrt. to some meaningful class (e.g. spelling variants of a certain word form) (default = False)
        - **KorAPUrl** - instead of specifying the `query` and `vc` string parameters, you can copy your KorAP query URL here from the browser
        - **metadataOnly** - determines whether queries should return only metadata without any snippets. This can also be useful to prevent access rewrites. (default = True)
        - **ql** - query language: `"poliqarp" | "cosmas2" | "annis" | "cql" | "fcsql"` (default = `"poliqarp"`)
        - **accessRewriteFatal** - abort if query or given vc had to be rewritten due to insufficient rights (not yet implemented) (default = `True`)
        - **verbose** - (default = `self.verbose`)
        - **expand** - bool that decides if `query` and `vc` parameters are expanded to all of their combinations (default = `len(vc) != len(query)`)

        Returns:
            DataFrame with columns `'query', 'totalResults', 'vc', 'webUIRequestUrl', 'total', 'f',
           'conf.low', 'conf.high'`.

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
        """
        return KorAPClient.frequencyQuery(self, *args, **kwargs)

    def collocationScoreQuery(self, node, collocate, vc="", **kwargs):
        """Get collocation scores for given node(s) and collocate(s).

        - **node** - target word
        - **collocate** - collocate of target word
        - **vc** - virtual corpus definition or list thereof  (default: "")
        - **lemmatizeNodeQuery** - logical, set to TRUE if node query should be lemmatized, i.e. x -> [tt/l=x]
        - **lemmatizeCollocateQuery** - logical, set to TRUE if collocate query should be lemmatized, i.e. x -> [tt/l=x]
        - **leftContextSize** - size of the left context window
        - **rightContextSize** - size of the right context window
        - **scoreFunctions** - named list of R (!) score functions of the form function(O1, O2, O, N, E, window_size), see e.g. KorAPClient.pmi
        - **smoothingConstant** - smoothing constant will be added to all observed values

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
        - **vc** - string or list of strings describing the virtual corpus in which the query should be performed. An empty string (default) means the whole corpus, as far as it is license-wise accessible.
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

        Returns:
            DataFrame with columns `'node', 'collocate', 'label', 'vc','webUIRequestUrl', 'w',  'leftContextSize',
               'rightContextSize', 'N', 'O', 'O1', 'O2', 'E', 'pmi', 'mi2', 'mi3', 'logDice', 'll'`

        Details:
            The collocation analysis is currently implemented on the client side, as some of the functionality is not yet provided by the KorAP backend. Mainly for this reason it is very slow (several minutes, up to hours), but on the other hand very flexible. You can, for example, perform the analysis in arbitrary virtual corpora, use complex node queries, and look for expression-internal collocates using the focus function (see examples and demo).
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
        - **fields** - (meta)data fields that will be fetched for every match (default = `["corpusSigle", "textSigle", "pubDate",  "pubPlace", "availability", "textClass", "matchStart", "matchEnd"]`)
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

