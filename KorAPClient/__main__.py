import argparse

from KorAPClient import KorAPConnection

prog = None if globals().get('__spec__') is None else 'python -m {}'.format(__spec__.name.partition('.')[0])
example = "example:\n  " + prog + ' "Hello World" "pubDate in 2018" "pubDate in 2019"'
parser = argparse.ArgumentParser(
    prog=prog,
    epilog=example,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Send a frequency query to the KorAP API and print results as tsv.')
parser.add_argument('-v', '--verbose', action="store_true")
parser.add_argument('-l', '--query-language', default="poliqarp")
parser.add_argument('-u', '--api-url', default=None)
parser.add_argument('query', nargs=1)
parser.add_argument('vc', nargs='*', help='virtual corpus definition[s]', default=[""])
args = parser.parse_args()

if __name__ == "__main__":
    if args.api_url is None:
        kcon = KorAPConnection(verbose=args.verbose)
    else:
        kcon = KorAPConnection(apiUrl=args.api_url, verbose=args.verbose)

    df = kcon.frequencyQuery(args.query[0],
                             vc=args.vc if len(args.vc) > 1 else args.vc[0], ql=args.query_language)
    print(df.to_csv(sep="\t"))
