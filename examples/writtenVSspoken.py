#!/usr/bin/python

from KorAPClient import KorAPConnection, KorAPClient
import plotly.express as px

df = KorAPConnection(verbose=True) \
    .frequencyQuery("sozusagen", vc=["corpusSigle=FOLK", "corpusSigle!=FOLK"])
df = KorAPClient.ipm(df)
df['error_y'] = df["conf.high"] - df["ipm"]
df['error_y_minus'] = df["ipm"] - df["conf.low"]
fig = px.bar(df, title="sozusagen", x="vc", y="ipm", error_y="error_y", error_y_minus="error_y_minus")
fig.show()
