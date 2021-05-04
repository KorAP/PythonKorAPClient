__pdoc__ = {'tests': False}

import rpy2.robjects.packages as packages
from rpy2.robjects.conversion import localconverter
import rpy2.robjects.pandas2ri as pandas2ri
import rpy2.robjects as robjects
from rpy2.robjects.methods import RS4
from packaging import version
import warnings

CURRENT_R_PACKAGE_VERSION = "0.6.1"

KorAPClient = packages.importr('RKorAPClient')
if version.parse(KorAPClient.__version__) < version.parse(CURRENT_R_PACKAGE_VERSION):
    warnings.warn("R-package RKorAPClient version " + KorAPClient.__version__  + " is outdated, please update.", DeprecationWarning)

pandas2ri.activate()

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
        - **cache** (dafault = True)
        """
        if 'userAgent' not in kwargs:
            kwargs["userAgent"] = "Python-KorAP-Client"
        kco = KorAPClient.KorAPConnection(*args, **kwargs)
        super().__init__(kco)

    def corpusStats(self, *args, **kwargs):
        """Query the size of the whole corpus or a virtual corpus specified by the vc argument.

            - vc = ""
            - verbose = kco@verbose
            - as.df = False

        Returns:
            `DataFrame`|`RS4`

        Example:
            ```
            $ df = kcon.corpusStats("pubDate in 2018 & textType=/Zeit.*/ & pubPlaceKey=IT", **{"as.df": True})
            $ df["tokens"]
            12150897
            ```
        """
        with localconverter(robjects.default_converter + pandas2ri.converter):
            return KorAPClient.corpusStats(self, *args, **kwargs)

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
        with localconverter(robjects.default_converter + pandas2ri.converter):
            return robjects.conversion.rpy2py(KorAPClient.frequencyQuery(self, *args, **kwargs))

    def collocationScoreQuery(self, node, collocate, vc="", **kwargs):
        """Get collocation scores for given node(s) and collocate(s).

        - **node** - target word
        - **collocate** - collocate of target word
        - **vc** - virtual corpus definition or list thereof  (default: "")
        - **lemmatizeNodeQuery** - logical, set to TRUE if node query should be lemmatized, i.e. x -> [tt/l=x]
        - **lemmatizeCollocateQuery** - logical, set to TRUE if collocate query should be lemmatized, i.e. x -> [tt/l=x]
        - **leftContextSize** - size of the left context window
        - **rightContextSize** - size of the right context window
        - **scoreFunctions** - named list of score functions of the form function(O1, O2, O, N, E, window_size), see e.g. pmi
        - smoothingConstant - smoothing constant will be added to all observed values

        Returns:
            DataFrame with columns `'node', 'collocate', 'label', 'vc','webUIRequestUrl', 'w',  'leftContextSize',
               'rightContextSize', 'N', 'O', 'O2', 'E', 'pmi', 'mi2', 'mi3', 'logDice' `

        Example:
            ```
            $ kcon = KorAPConnection(verbose=True)
            $ df = kcon.collocationScoreQuery("Grund", "triftiger")
            ```
        """
        with localconverter(robjects.default_converter + pandas2ri.converter):
            if type(node) is list:
                node = robjects.StrVector(node)
            if type(collocate) is list:
                collocate = robjects.StrVector(collocate)
            if type(vc) is list:
                vc = robjects.StrVector(vc)

            return robjects.conversion.rpy2py(KorAPClient.collocationScoreQuery(self, node, collocate, vc, **kwargs))

    def corpusQuery(self, *args, **kwargs):
        """Query search term(s).

        - **query** - query string or list of query strings
        - **vc** - virtual corpus definition or list thereof (default: "")
        - **KorAPUrl** - instead of specifying the `query` and `vc` string parameters, you can copy your KorAP query URL here from the browser
        - **metadataOnly** - determines whether queries should return only metadata without any snippets. This can also be useful to prevent access rewrites. (default = True)
        - **ql** - query language: `"poliqarp" | "cosmas2" | "annis" | "cql" | "fcsql"` (default = `"poliqarp"`)
        - **fields** - (meta)data fields that will be fetched for every match (default = `["corpusSigle", "textSigle", "pubDate",  "pubPlace", "availability", "textClass"]`)
        - **verbose** - (default = `self.verbose`)

        Returns:
            `KorAPQuery` | `pandas.DataFrame`

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

        Returns:
            `KorAPQuery`
        """
        return KorAPClient.fetchNext(self, *args, **kwargs)

    def fetchRest(self, *args, **kwargs):
        """Fetch remaining query results

        - **verbose**

        Returns:
            `KorAPQuery`
        """
        return KorAPClient.fetchRest(self, *args, **kwargs)

    def fetchAll(self, *args, **kwargs):
        """Fetch all query results

        - **verbose**

        Returns:
            `KorAPQuery`

        Example:
            See `KorAPConnection.corpusQuery`.
        """
        return KorAPClient.fetchAll(self, *args, **kwargs)
