# Python Client Support
Currently, there is no native KorAP client library for Python. 
With [rpy2](https://rpy2.github.io/), however, you can simply use the [KorAP client library for R](https://github.com/KorAP/RKorAPClient) from within Python.

## Using the RKorAPClient from within Python
### Installing Dependencies
#### Ubuntu Linux
```shell script
sudo apt install r-base python3-rpy2 python3-pandas
echo 'install.packages("RKorAPClient", repos="http://cran.rstudio.com/")' | R --vanilla
pip3 install plotly-express
```
#### Alternative Dependencies Installation
- install the RKorAP client as described in it's [installation section](https://github.com/KorAP/RKorAPClient#installation)
- install rpy2
  ```shell script
  pip install rpy2
  ```
  Possibly, you need to let it know where your R packages are installed, with e.g.:
  ```shell script
  # export R_LIBS=/home/$HOME/R/x86_64-redhat-linux-gnu-library/3.6
  ```
- install [Plotly Express](https://plotly.com/python/plotly-express/) to run the [examples](examples) with visualizations:
  ```shell script
  pip install plotly.express
  ```
#### Examples
#### Frequencies over years and countries
```python
import rpy2.robjects.packages as packages
import rpy2.robjects.pandas2ri as pandas2ri
import plotly.express as px
pandas2ri.activate()

QUERY = "Hello World"
YEARS = range(2010, 2019)
COUNTRIES = ["DE", "CH"]

RKorAPClient = packages.importr('RKorAPClient')
kcon = RKorAPClient.KorAPConnection(verbose=True)

vcs = ["textType=/Zeit.*/ & pubPlaceKey=" + c + " & pubDate in " + str(y) for c in COUNTRIES for y in YEARS]
df = RKorAPClient.ipm(RKorAPClient.frequencyQuery(kcon, QUERY, vcs))
df['Year'] = [y for c in COUNTRIES for y in YEARS]
df['Country'] = [c for c in COUNTRIES for y in YEARS]

fig = px.line(df, title=QUERY, x="Year", y="ipm", color="Country",
              error_y="conf.high", error_y_minus="conf.low")
fig.show()
```
[Frequency per million words of “Hello World“ in DE vs. AT from 2010 to 2018 in newspapers and magazines](figures/hello-world.png)

### Accessed API Services
By using the KorAPClient you agree to the respective terms of use of the accessed KorAP API services which will be printed upon opening a connection.

## Development and License

**Author**: [Marc Kupietz](http://www1.ids-mannheim.de/zfo/personal/kupietz/)

Copyright (c) 2020, [Leibniz Institute for the German Language](http://www.ids-mannheim.de/), Mannheim, Germany

This package is developed as part of the [KorAP](http://korap.ids-mannheim.de/)
Corpus Analysis Platform at the Leibniz Institute for German Language
([IDS](http://www.ids-mannheim.de/)).

It is published under the [BSD-2 License](LICENSE).

## Contributions

Contributions are very welcome!

Your contributions should ideally be committed via our [Gerrit server](https://korap.ids-mannheim.de/gerrit/)
to facilitate reviewing (see [Gerrit Code Review - A Quick Introduction](https://korap.ids-mannheim.de/gerrit/Documentation/intro-quick.html)
if you are not familiar with Gerrit). However, we are also happy to accept comments and pull requests
via GitHub.

Please note that unless you explicitly state otherwise any
contribution intentionally submitted for inclusion into this software shall –
as this software itself – be under the [BSD-2 License](LICENSE).

## References

- Kupietz, Marc / Margaretha, Eliza / Diewald, Nils / Lüngen, Harald / Fankhauser, Peter (2019): [What’s New in EuReCo? Interoperability, Comparable Corpora, Licensing](https://nbn-resolving.org/urn:nbn:de:bsz:mh39-90261). In: Bański, Piotr/Barbaresi, Adrien/Biber, Hanno/Breiteneder, Evelyn/Clematide, Simon/Kupietz, Marc/Lüngen, Harald/Iliadi, Caroline (eds.): [*Proceedings of the International Corpus Linguistics Conference 2019 Workshop "Challenges in the Management of Large Corpora (CMLC-7)"*](https://ids-pub.bsz-bw.de/solrsearch/index/search/searchtype/collection/id/21038), 22nd of July Mannheim: Leibniz-Institut für Deutsche Sprache, 33-39.

- Kupietz, Marc / Diewald, Nils / Margaretha, Eliza (forthcoming): RKorAPClient: An R package for accessing the German Reference Corpus DeReKo via KorAP. In: Proceedings of the Twelfth International Conference on Language Resources and Evaluation (LREC 2020). Marseille/Paris: European Language Resources Association (ELRA). 

