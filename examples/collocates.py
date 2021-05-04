#!/usr/bin/env python3

from KorAPClient import KorAPConnection
import plotly.express as px
import pandas as pd

startYear = 1991
endYear = 2020
span = 5

NODE = "Ei"
COLLOCATES = ["pellen", "schälen"]
COUNTRIES = ["DE", "AT", "CH"]

TITLE = f"Collocation strength of <i>{NODE} + {' / '.join(COLLOCATES)} </i> in {', '.join(COUNTRIES)} {startYear}-{endYear}"

YEARS = [y for y in range(startYear, endYear, span)]

# build all combinations of all variables
df = pd.DataFrame(YEARS, columns=["year"]) \
    .merge(pd.DataFrame(COUNTRIES, columns=["Country"]), how='cross') \
    .merge(pd.DataFrame(COLLOCATES, columns=["Collocate"]), how='cross')

# add column with virtual corpus specifications based on Country and year variables
df['vc'] = [
    f"textType=/Zeit.*/ & pubPlaceKey={df['Country'][i]} & pubDate since {df['year'][i]} & pubDate until {df['year'][i] + span - 1} "
    for i in range(0, len(df.index))]

# add column with label for x axis
df['Period'] = [f"{df['year'][i]}-{df['year'][i] + span - 1}" for i in range(0, len(df.index))]

# connect to KorAP API server
kcon = KorAPConnection(verbose=True)

# perform the actual KorAP query
results = kcon.collocationScoreQuery(NODE, df['Collocate'], df['vc'], lemmatizeNodeQuery=True,
                                     lemmatizeCollocateQuery=True)

# join query result columns (axis=1 ...) with condition information columns
# (why is reset_index needed?)
df = pd.concat([df.reset_index(drop=True), results.reset_index(drop=True)], axis=1)

fig = px.line(df, title=TITLE, x="Period", y="logDice", color="Country", line_dash="Collocate")
fig.show()
# fig.write_image(f"{NODE}_collocates_{startYear}-{endYear}_in_{'_'.join(COUNTRIES)}.png")
