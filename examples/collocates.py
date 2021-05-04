from KorAPClient import KorAPClient, KorAPConnection
import plotly.express as px

YEARS = range(1951, 2020, 10)

kcon = KorAPConnection(verbose=True)

vcs = ["textType=/Zeit.*/ & pubDate since " + str(y) + " & pubDate until " + str(y + 9) for y in YEARS]
df = kcon.collocationScoreQuery("Gefahr", "laufen", vcs, lemmatizeNodeQuery=True,
                                lemmatizeCollocateQuery=True)
df['Decade'] = [str(y) + "-" + str(y + 9) for y in YEARS]

fig = px.line(df, title="Collocation strength:", x="Decade", y="logDice")
fig.show()
