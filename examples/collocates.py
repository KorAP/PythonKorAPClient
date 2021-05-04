from KorAPClient import KorAPConnection
import plotly.express as px
import pandas as pd

NODE = "Maßnahme"
YEARS = [y for y in range(1996, 2020, 5)]
COUNTRIES = ["DE", "CH"]
COLLOCATES = ["griffig", "wirksam"]

TITLE = f"Collocation strength of {NODE} + {COLLOCATES} in {COUNTRIES} over time"

df = pd.DataFrame(YEARS, columns=["year"]) \
    .merge(pd.DataFrame(COUNTRIES, columns=["Country"]), how='cross') \
    .merge(pd.DataFrame(COLLOCATES, columns=["Collocate"]), how='cross')
df['vc'] = [
    f"textType=/Zeit.*/ & pubPlaceKey={df['Country'][i]} & pubDate since {df['year'][i]} & pubDate until {df['year'][i] + 9}"
    for i in range(0, len(df.index))]
df['Period'] = [f"{df['year'][i]}-{df['year'][i] + 5}" for i in range(0, len(df.index))]
print(df)

kcon = KorAPConnection(verbose=True)

results = kcon.collocationScoreQuery(NODE, df['Collocate'], df['vc'], lemmatizeNodeQuery=True,
                                     lemmatizeCollocateQuery=True)

# join query result columns (axis=1 ...) with condition information columns
# (why are these reset_indexex needed?)
df =  pd.concat([df.reset_index(drop=True), results.reset_index(drop=True)], axis=1)

fig = px.line(df, title=TITLE, x="Period", y="logDice", color="Country", line_dash="Collocate")
fig.update_layout(template="plotly_white", font_family="Fira Sans Condensed")
fig.show()
fig.write_image("../figures/collocates.png")
fig.write_image("../figures/collocates.pdf")