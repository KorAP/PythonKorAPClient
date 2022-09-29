#!/usr/bin/env python3
import altair as alt
from KorAPClient import KorAPClient, KorAPConnection, expand_grid

QUERY = "Hello World"
df = expand_grid({"Year": range(2010, 2019), "Country": ["DE", "CH"]})
df["vc"] = "textType=/Zeit.*/ & pubPlaceKey = " + df.Country + " & pubDate in " + list(map(str, df.Year))

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
