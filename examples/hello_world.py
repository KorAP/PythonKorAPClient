#!/usr/bin/env python3
from KorAPClient import KorAPClient, KorAPConnection
import plotly.express as px

QUERY = "Hello World"
YEARS = range(2010, 2019)
COUNTRIES = ["DE", "CH"]

kcon = KorAPConnection(verbose=True)

vcs = [f"textType=/Zeit.*/ & pubPlaceKey={c} & pubDate in {y}" for c in COUNTRIES for y in YEARS]
df = KorAPClient.ipm(kcon.frequencyQuery(QUERY, vcs))
print(df)

df['Year'] = [y for c in COUNTRIES for y in YEARS]
df['Country'] = [c for c in COUNTRIES for y in YEARS]
df['error_y'] = df["conf.high"] - df["ipm"]
df['error_y_minus'] = df["ipm"] - df["conf.low"]

fig = px.line(df, title=QUERY, x="Year", y="ipm", color="Country",
              error_y="error_y", error_y_minus="error_y_minus")
fig.show()
