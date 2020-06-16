import rpy2.robjects.packages as packages
import rpy2.robjects.pandas2ri as pandas2ri
import plotly.express as px
pandas2ri.activate()

QUERY = "Hello World"
YEARS = range(2010, 2019)
COUNTRIES = ["DE", "CH"]

RKorAPClient = packages.importr('RKorAPClient')
kcon = RKorAPClient.KorAPConnection(verbose=True)

vcs = ["textType=/Zeit.*/ & pubPlaceKey=" + c + " & pubDate in " + str(y) for c in COUNTRIES for y in YEARS]
df = RKorAPClient.ipm(RKorAPClient.frequencyQuery(kcon, QUERY, vcs))
df['Year'] = [y for c in COUNTRIES for y in YEARS]
df['Country'] = [c for c in COUNTRIES for y in YEARS]

fig = px.line(df, title=QUERY, x="Year", y="ipm", color="Country",
              error_y="conf.high", error_y_minus="conf.low")
fig.show()
