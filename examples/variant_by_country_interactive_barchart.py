import altair as alt

from KorAPClient import KorAPConnection, KorAPClient

COUNTRIES = ["DE", "AT", "CH"]

kcon = KorAPConnection(verbose=True)
df = kcon.frequencyQuery(query=['"Wissenschaftler.*"', '"Wissenschafter.*"'],
                         vc=[f"pubPlaceKey = {c}" for c in COUNTRIES],
                         **{"as.alternatives": True})

df["Land"] = KorAPClient.queryStringToLabel(df.vc)

alt.Chart(df).mark_bar().encode(
    y="Land",
    x=alt.X("f", title="Anteil", axis=alt.Axis(format='%')),
    color=alt.Color("query", title="Variante"),
    href="webUIRequestUrl",
    tooltip=[alt.Tooltip('f', format=".1%", title="Anteil")]
).show()

