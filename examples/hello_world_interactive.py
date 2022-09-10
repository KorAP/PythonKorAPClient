#!/usr/bin/env python3
import altair as alt

from KorAPClient import KorAPClient, KorAPConnection

QUERY = "Hello World"
YEARS = range(2010, 2019)
COUNTRIES = ["DE", "CH"]

kcon = KorAPConnection(verbose=True)

vcs = [f"textType=/Zeit.*/ & pubPlaceKey={c} & pubDate in {y}" for c in COUNTRIES for y in YEARS]
df = KorAPClient.ipm(kcon.frequencyQuery(QUERY, vcs))
print(df)

df['Year'] = [y for c in COUNTRIES for y in YEARS]
df['Country'] = [c for c in COUNTRIES for y in YEARS]
df['tooltip'] = "ctrl+click to open concordances in new tab"

band = alt.Chart(df).mark_errorband().encode(
    y=alt.Y("conf.low", title=""),
    y2="conf.high",
    x="Year",
    color="Country",
    tooltip=["Country", "Year", alt.Tooltip("ipm", format=".2f")]
)

line = alt.Chart(df).mark_line(point=True).encode(
    y="ipm",
    x="Year",
    color="Country",
    href="webUIRequestUrl",
    tooltip="tooltip"
)

(band + line).show()
