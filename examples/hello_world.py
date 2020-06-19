#!/usr/bin/env python3
from KorAPClient import KorAPClient
import plotly.express as px

QUERY = "Hello World"
YEARS = range(2010, 2019)
COUNTRIES = ["DE", "CH"]

kcon = KorAPClient.KorAPConnection(verbose=True)

vcs = ["textType=/Zeit.*/ & pubPlaceKey=" + c + " & pubDate in " + str(y) for c in COUNTRIES for y in YEARS]
df = KorAPClient.ipm(KorAPClient.frequencyQuery(kcon, QUERY, vcs))
df['Year'] = [y for c in COUNTRIES for y in YEARS]
df['Country'] = [c for c in COUNTRIES for y in YEARS]

fig = px.line(df, title=QUERY, x="Year", y="ipm", color="Country",
              error_y="conf.high", error_y_minus="conf.low")
fig.show()
