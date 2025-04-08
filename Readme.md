# KorAP web service client package for Python

[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![CI check](https://github.com/KorAP/PythonKorAPClient/workflows/PythonKorAPClient%20CI%20unit%20test/badge.svg)](https://github.com/KorAP/PythonKorAPClient/actions?workflow=PythonKorAPClient%20CI%20unit%20test)
[![Last commit](https://img.shields.io/github/last-commit/KorAP/PythonKorAPClient.svg)](https://github.com/KorAP/PythonKorAPClient/issues)
[![GitHub closed issues](https://img.shields.io/github/issues-raw/KorAP/PythonKorAPClient.svg)](https://github.com/KorAP/PythonKorAPClient/issues)
[![GitHub issues](https://img.shields.io/github/issues-closed-raw/KorAP/PythonKorAPClient.svg)](https://github.com/KorAP/PythonKorAPClient/issues)
[![GitHub license](https://img.shields.io/github/license/KorAP/PythonKorAPClient)](https://github.com/KorAP/PythonKorAPClient/blob/master/LICENSE)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/KorAPClient)
![PyPI - Downloads](https://img.shields.io/pypi/dm/KorAPClient)
## Description
Python client wrapper package to access the [web service API](https://github.com/KorAP/Kustvakt/wiki) of the [KorAP Corpus Analysis Platform](https://korap.ids-mannheim.de/) developed at [IDS Mannheim](http://www.ids-mannheim.de/).
Currently, this is no native Python package. Internally, it uses [KorAP's client package for R](http://github.com/KorAP/RKorAPClient)
via [rpy2](https://rpy2.github.io/). The latter also automatically translates between R data frames (or [tibbles](https://tibble.tidyverse.org/)) and [pandas DataFrames](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html). 

## Installation

#### 1. Install latest R version for your OS, following the instructions from [CRAN](https://cran.r-project.org/bin/)

#### Linux only: Install system dependencies

```shell script
#### Debian / Ubuntu
sudo apt install r-base-dev r-cran-rcpp r-cran-cpp11 libcurl4-gnutls-dev libxml2-dev libsodium-dev libsecret-1-dev libfontconfig1-dev libssl-dev libv8-dev python3-dev python3-pip python3-rpy2 python3-pandas python3-pytest libdeflate-dev r-cran-rcpparmadillo

#### Fedora / CentOS / RHEL
sudo yum install -y R R-devel libcurl-devel openssl-devel libxml2-devel libsodium-devel python3-pandas
```

#### 2. Install the RKorAPClient package

Start R and run:

```R
install.packages('RKorAPClient', repos='https://cloud.r-project.org/')
```

or install RKorAPClient from the package installation menu entry.

#### 3. Install the Python package

On Linux and macOS:

```shell script
# py -m pip install KorAPClient -U
python3 -m pip install KorAPClient -U # --break-system-packages
```

On Windows:

```shell script
# py -m pip install pip -U
py -m pip install KorAPClient -U
```

## Documentation
The core classes and methods to access the KorAP API are documented in the [KorAPClient API documentation](https://korap.github.io/PythonKorAPClient/KorAPClient/).
For additional, mostly static helper functions, please refer to the [Reference Manual of RKorAPClient](https://cran.r-project.org/web/packages/RKorAPClient/RKorAPClient.pdf) for now. 
For translating R syntax to Python and vice versa, refer to the [rpy2 Documentation](https://rpy2.github.io/doc/latest/html/index.html).

Please note that some arguments in the original RKorAPClient functions use characters that are not allowed in Python keyword argument names.
For these cases, you can however use Python's `**kwargs` syntax.
For example, to let `frequencyQuery` interpret queries as queries for alternative variants and make it return their proportions instead of relative frequencies,
you can write:

```python
from KorAPClient import KorAPConnection
KorAPConnection(verbose=True) \
    .frequencyQuery(['"Wissenschaftler.*"', '"Wissenschafter.*"'],\
                    **{"as.alternatives": True})
```

|    | query               |   totalResults | vc   | webUIRequestUrl                                                        |   total |        f |   conf.low |   conf.high |
|---:|:--------------------|---------------:|:-----|:-----------------------------------------------------------------------|--------:|---------:|-----------:|------------:|
|  1 | "Wissenschaftler.*" |         942053 |      | https://korap.ids-mannheim.de/?q=%22Wissenschaftler.%2a%22&ql=poliqarp | 1080268 | 0.872055 |   0.871423 |    0.872684 |
|  2 | "Wissenschafter.*"  |         138215 |      | https://korap.ids-mannheim.de/?q=%22Wissenschafter.%2a%22&ql=poliqarp  | 1080268 | 0.127945 |   0.127316 |    0.128577 |


### Authorization

In order to retrieve KWIC data from copyrighted texts, you need to authenticate yourself and authorize the client to act on behalf of you.
There are different ways to do this (see [Authorization Section of RKorAPClient](https://github.com/KorAP/RKorAPClient#-authorizing-rkorapclient-applications-to-access-restricted-kwics-from-copyrighted-texts)).
The easiest way is to use the `auth()` method of the `KorAPConnection` class. This will open a browser window and ask you to log in with your KorAP account.

```python
from KorAPClient import KorAPConnection
kcon = KorAPConnection().auth()
```

## Examples
#### Frequencies of "Hello World" over years and countries
```python
from KorAPClient import KorAPClient, KorAPConnection
import altair as alt
import pandas as pd

QUERY = "Hello World"
df = pd.DataFrame(range(2010, 2019), columns=["Year"], dtype=str) \
    .merge(pd.DataFrame(["DE", "CH"], columns=["Country"]), how="cross")
df["vc"] = "textType=/Zeit.*/ & pubPlaceKey = " + df.Country + " & pubDate in " + df.Year
df = KorAPClient.ipm(KorAPConnection().frequencyQuery(QUERY, df.vc)).merge(df)

alt.Chart(df).mark_line(point=True).encode(y="ipm", x="Year:T", color="Country", href="webUIRequestUrl") \
    .properties(title=QUERY).show()
```
[![Frequency per million words of “Hello World“ in DE vs. CH from 2010 to 2018 in newspapers and magazines](https://raw.githubusercontent.com/KorAP/PythonKorAPClient/master/figures/hello-world.png)<!-- -->](https://korap.github.io/PythonKorAPClient/figures/hello_world.html)


### Identify *in … setzen* light verb constructions by the `collocationAnalysis` method
[![Lifecycle:experimental](https://lifecycle.r-lib.org/articles/figures/lifecycle-experimental.svg)](https://www.tidyverse.org/lifecycle/#experimental)
```python
from KorAPClient import KorAPConnection

kcon = KorAPConnection(verbose=True).auth()
results = kcon.collocationAnalysis("focus(in [tt/p=NN] {[tt/l=setzen]})",
                                   leftContextSize=1,
                                   rightContextSize=0,
                                   exactFrequencies=False,
                                   searchHitsSampleLimit=1000,
                                   topCollocatesLimit=20)
results['collocate'] = "[" + results['collocate'] +"](" + results['webUIRequestUrl'] +")"
print(results[['collocate', 'logDice', 'pmi', 'll']].head(10).round(2).to_markdown(floatfmt=".2f"))
```
|    | collocate                                                                                                                                                  |   logDice |   pmi |        ll |
|---:|:-----------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|------:|----------:|
|  1 | [Szene](https://korap.ids-mannheim.de/?q=Szene%20focus%28in%20%5btt%2fp%3dNN%5d%20%7b%5btt%2fl%3dsetzen%5d%7d%29&ql=poliqarp)                              |     10.37 | 11.54 | 824928.58 |
|  2 | [Gang](https://korap.ids-mannheim.de/?q=Gang%20focus%28in%20%5btt%2fp%3dNN%5d%20%7b%5btt%2fl%3dsetzen%5d%7d%29&ql=poliqarp)                                |      9.65 | 10.99 | 366993.93 |
|  3 | [Verbindung](https://korap.ids-mannheim.de/?q=Verbindung%20focus%28in%20%5btt%2fp%3dNN%5d%20%7b%5btt%2fl%3dsetzen%5d%7d%29&ql=poliqarp)                    |      9.20 | 10.34 | 347644.75 |
|  4 | [Kenntnis](https://korap.ids-mannheim.de/?q=Kenntnis%20focus%28in%20%5btt%2fp%3dNN%5d%20%7b%5btt%2fl%3dsetzen%5d%7d%29&ql=poliqarp)                        |      9.15 | 10.67 | 206902.89 |
|  5 | [Bewegung](https://korap.ids-mannheim.de/?q=Bewegung%20focus%28in%20%5btt%2fp%3dNN%5d%20%7b%5btt%2fl%3dsetzen%5d%7d%29&ql=poliqarp)                        |      8.80 |  9.91 | 264577.07 |
|  6 | [Brand](https://korap.ids-mannheim.de/?q=Brand%20focus%28in%20%5btt%2fp%3dNN%5d%20%7b%5btt%2fl%3dsetzen%5d%7d%29&ql=poliqarp)                              |      8.76 |  9.97 | 210654.43 |
|  7 | [Anführungszeichen](https://korap.ids-mannheim.de/?q=Anf%c3%bchrungszeichen%20focus%28in%20%5btt%2fp%3dNN%5d%20%7b%5btt%2fl%3dsetzen%5d%7d%29&ql=poliqarp) |      8.06 | 12.52 |  54148.31 |
|  8 | [Kraft](https://korap.ids-mannheim.de/?q=Kraft%20focus%28in%20%5btt%2fp%3dNN%5d%20%7b%5btt%2fl%3dsetzen%5d%7d%29&ql=poliqarp)                              |      7.94 |  8.91 | 189399.70 |
|  9 | [Beziehung](https://korap.ids-mannheim.de/?q=Beziehung%20focus%28in%20%5btt%2fp%3dNN%5d%20%7b%5btt%2fl%3dsetzen%5d%7d%29&ql=poliqarp)                      |      6.92 |  8.29 |  37723.54 |
| 10 | [Relation](https://korap.ids-mannheim.de/?q=Relation%20focus%28in%20%5btt%2fp%3dNN%5d%20%7b%5btt%2fl%3dsetzen%5d%7d%29&ql=poliqarp)                        |      6.64 | 10.24 |  17105.84 |

## Command Line Invocation
The Python KorAP client can also be called from the command line and shell scripts:
```shell script
$ korapclient -h
usage: python -m KorAPClient [-h] [-v] [-l QUERY_LANGUAGE] [-u API_URL] [-c VC [VC ...]] [-q QUERY [QUERY ...]]

Send a query to the KorAP API and print results as tsv.

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose
  -l QUERY_LANGUAGE, --query-language QUERY_LANGUAGE
  -u API_URL, --api-url API_URL
                        Specify this to access a corpus other that DeReKo.
  -c VC [VC ...], --vc VC [VC ...]
                        virtual corpus definition[s]
  -q QUERY [QUERY ...], --query QUERY [QUERY ...]
                        If not specified only the size of the virtual corpus will be queried.

example:
  python -m KorAPClient -v --query "Hello World" "Hallo Welt" --vc "pubDate in 2017" "pubDate in 2018" "pubDate in 2019"
```

### Accessed API Services
By using the KorAPClient you agree to the respective terms of use of the accessed KorAP API services which will be printed upon opening a connection.

## Development and License

**Authors**: [Marc Kupietz](https://www.ids-mannheim.de/digspra/personal/kupietz/), [Tim Feldmüller](https://www.ids-mannheim.de/digspra/personal/feldmueller)

Copyright (c) 2025, [Leibniz Institute for the German Language](http://www.ids-mannheim.de/), Mannheim, Germany

This package is developed as part of the [KorAP](http://korap.ids-mannheim.de/)
Corpus Analysis Platform at the Leibniz Institute for the German Language
([IDS](http://www.ids-mannheim.de/)).

It is published under the [BSD-2 License](LICENSE.txt).

**Contributors**: [Ines Pisetta](https://github.com/inlpi), [Nils Diewald](https://github.com/akron)

**To cite this work,** please refer to: Kupietz et al. (2020, 2022), below.

## Contributions

Contributions are very welcome!

Your contributions should ideally be committed via our [Gerrit server](https://korap.ids-mannheim.de/gerrit/)
to facilitate reviewing (see [Gerrit Code Review - A Quick Introduction](https://korap.ids-mannheim.de/gerrit/Documentation/intro-quick.html)
if you are not familiar with Gerrit). However, we are also happy to accept comments and pull requests
via GitHub.

Please note that unless you explicitly state otherwise any
contribution intentionally submitted for inclusion into this software shall –
as this software itself – be under the [BSD-2 License](LICENSE.txt).

## References

- Kupietz, Marc / Diewald, Nils / Margaretha, Eliza (2020): [RKorAPClient: An R package for accessing the German Reference Corpus DeReKo via KorAP](http://www.lrec-conf.org/proceedings/lrec2020/pdf/2020.lrec-1.867.pdf). In: Calzolari, Nicoletta, Frédéric Béchet, Philippe Blache, Khalid Choukri, Christopher Cieri,  Thierry Declerck, Sara Goggi, Hitoshi Isahara, Bente Maegaard, Joseph Mariani, Hélène Mazo, Asuncion Moreno, Jan Odijk, Stelios Piperidis (eds.): [Proceedings of The 12th Language Resources and Evaluation Conference (LREC 2020)](http://www.lrec-conf.org/proceedings/lrec2020/LREC-2020.pdf). Marseille: European Language Resources Association (ELRA), 7017-7023.

- Kupietz, Marc / Diewald, Nils / Margaretha, Eliza (2022): Building paths to corpus data: A multi-level least effort and maximum return approach. In Fišer, Darja / Witt, Andreas (eds.): [CLARIN. The infrastructure for language resources.](https://www.degruyter.com/document/isbn/9783110767377/html) Berlin: deGruyter.
