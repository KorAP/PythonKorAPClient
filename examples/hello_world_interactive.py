#!/usr/bin/env python3
import altair as alt
import pandas as pd
from KorAPClient import KorAPClient, KorAPConnection

QUERY = "Hello World"
YEARS = range(2010, 2019)
COUNTRIES = ["DE", "CH"]

df = pd.DataFrame(YEARS, columns=["Year"], dtype=str).merge(pd.DataFrame(COUNTRIES, columns=["Country"]), how="cross")
df["vc"] = "textType=/Zeit.*/ & pubPlaceKey = " + df.Country + " & pubDate in " + df.Year

kcon = KorAPConnection(verbose=True)

df = KorAPClient.ipm(kcon.frequencyQuery(QUERY, df.vc)).merge(df)
df['tooltip'] = "ctrl+click to open concordances in new tab"

band = alt.Chart(df).mark_errorband().encode(
    y=alt.Y("conf.low", title="ipm"),
    y2="conf.high",
    x="Year:T",
    color="Country",
    tooltip=["Country", "Year", alt.Tooltip("ipm", format=".2f")]
)

line = alt.Chart(df).mark_line(point=True).encode(
    y="ipm",
    x="Year:T",
    color="Country",
    href="webUIRequestUrl",
    tooltip="tooltip"
)

(band + line).show()
