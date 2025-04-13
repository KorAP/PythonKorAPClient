from KorAPClient import KorAPConnection
from rpy2.robjects import r

# As base, use the fiction corpus DeLiKo@DNB (see <https://doi.org/10.5281/zenodo.14943116>)
kcon = KorAPConnection(KorAPUrl="https://korap.dnb.de/", verbose=True).auth()

r['set.seed'](42) # Set the seed for reproducibility, will in future be exported by KorAPClient
q = kcon.corpusQuery("[tt/l=Wange]", metadataOnly=False)
q = q.fetchNext(maxFetch=1000, randomizePageOrder=True)

# Calculate the maximum width for the left and right columns
max_left_width = max(len(row['tokens.left']) for _, row in q.slots['collectedMatches'].iterrows())
max_right_width = max(len(row['tokens.right']) for _, row in q.slots['collectedMatches'].iterrows())

# Iterate through all rows of the collected matches
i = 0
for _, row in q.slots['collectedMatches'].iterrows():
    left_context, match, right_context = (row[col].replace("\t", " ") for col in
                                          ['tokens.left', 'tokens.match', 'tokens.right'])

    # ANSI escapes for bold text
    bold_start = "\033[1m"
    bold_end = "\033[0m"

    print(f"{i:>5} {left_context:>{max_left_width}} {bold_start}{match}{bold_end} {right_context:<{max_right_width}}")
    i = i + 1
