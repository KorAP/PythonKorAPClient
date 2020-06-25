import rpy2.robjects.packages as packages
import rpy2.robjects.pandas2ri as pandas2ri
from rpy2.robjects.methods import RS4

KorAPClient = packages.importr('RKorAPClient')
pandas2ri.activate()


class KorAPConnection(RS4):
    def __init__(self, *args, **kwargs):
        kco = KorAPClient.KorAPConnection(*args, **kwargs)
        super().__init__(kco)

    def corpusStats(self, *args, **kwargs):
        return KorAPClient.corpusStats(self, *args, **kwargs)

    def frequencyQuery(self, *args, **kwargs):
        return KorAPClient.frequencyQuery(self, *args, **kwargs)

    def corpusQuery(self, *args, **kwargs):
        return KorAPQuery(self, *args, **kwargs)


class KorAPQuery(RS4):
    def __init__(self, *args, **kwargs):
        kco = KorAPClient.corpusQuery(*args, **kwargs)
        super().__init__(kco)

    def fetchNext(self, *args, **kwargs):
        return KorAPClient.fetchNext(self, *args, **kwargs)

    def fetchRest(self, *args, **kwargs):
        return KorAPClient.fetchRest(self, *args, **kwargs)

    def fetchAll(self, *args, **kwargs):
        return KorAPClient.fetchAll(self, *args, **kwargs)
