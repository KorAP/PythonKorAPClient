import rpy2.robjects.pandas2ri as pandas2ri
import rpy2.robjects.packages as packages
KorAPClient = packages.importr('RKorAPClient')
pandas2ri.activate()
