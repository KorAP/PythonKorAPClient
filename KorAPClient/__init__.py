__pdoc__ = { 'tests': False }
import rpy2.robjects.packages as packages
import rpy2.robjects.pandas2ri as pandas2ri
from rpy2.robjects.methods import RS4
from pandas import DataFrame

KorAPClient = packages.importr('RKorAPClient')
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

        Parameters
        ----------
        **kwargs :
            vc = "", verbose = kco@verbose, as.df = False

        Returns
        -------
        DataFrame|RS4
        """
        return KorAPClient.corpusStats(self, *args, **kwargs)

    def frequencyQuery(self, *args, **kwargs):
        """Query relative frequency of search term(s).

        - **query** – query string
        - **vc** - virtual corpus definition
        - **conf.level** – (default = 0.95)
        - **as.alternatives** – (default = False)
        - **KorAPUrl** – instead of providing the query and vc string parameters, you can use a copy your KorAP query URL here
        - **metadataOnly** – determines whether queries should return only metadata without any snippets. This can also be useful to prevent access rewrites. (default = True)
        - **ql** – query language: `poliqarp|cosmas2|annis|cql|fcsql` (default = `"poliqarp"`)
        - **accessRewriteFatal** – (default = `True`)
        - **verbose** – (default = `self.verbose`)
        - **expand**: – (default = `len(vc) != len(query)`)

        Returns
        -------
        DataFrame
        """
        return KorAPClient.frequencyQuery(self, *args, **kwargs)

    def corpusQuery(self, *args, **kwargs):
        """Query search term(s).

        - **query** – query string
        - **vc** - virtual corpus definition
        - **KorAPUrl** – instead of providing the query and vc string parameters, you can copy your KorAP query URL here
        - **metadataOnly** – determines whether queries should return only metadata without any snippets. This can also be useful to prevent access rewrites. (default = True)
        - **ql** – query language: `poliqarp|cosmas2|annis|cql|fcsql` (default = `"poliqarp"`)
        - **fields** – (meta)data fields that will be fetched for every match (default = `["corpusSigle", "textSigle", "pubDate",  "pubPlace", "availability", "textClass"]`)
        - **verbose** – (default = `self.verbose`)

        Returns:
            KorAPQuery|DataFrame
        """
        return KorAPQuery(self, *args, **kwargs)


class KorAPQuery(RS4):
    """Query to a KorAP server."""


    def __init__(self, *args, **kwargs):
        kco = KorAPClient.corpusQuery(*args, **kwargs)
        super().__init__(kco)

    def fetchNext(self, *args, **kwargs):
        """Fetch next couple of query results

        - **offset** start offset for query results to fetch
        - **maxFetch** maximum number of query results to fetch
        - **verbose**

        Returns:
            KorAPQuery
        """
        return KorAPClient.fetchNext(self, *args, **kwargs)

    def fetchRest(self, *args, **kwargs):
        """Fetch remaining query results

        - **offset** start offset for query results to fetch
        - **maxFetch** maximum number of query results to fetch
        - **verbose**

        Returns:
            KorAPQuery
        """
        return KorAPClient.fetchRest(self, *args, **kwargs)

    def fetchAll(self, *args, **kwargs):
        """Fetch all query results

        - **offset** start offset for query results to fetch
        - **maxFetch** maximum number of query results to fetch
        - **verbose**

        Returns:
            KorAPQuery
        """
        return KorAPClient.fetchAll(self, *args, **kwargs)
