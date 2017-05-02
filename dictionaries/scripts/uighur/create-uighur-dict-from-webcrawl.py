import optparse
import os
from collections import defaultdict

optparser = optparse.OptionParser()
optparser.add_option("-d", "--directory", dest="directory", default="uighur/", help="Directory with dictionaries")
optparser.add_option("-o", "--original_dictionary", dest="original_dictionary", help="Original dictionary to be used for re-ordering")
(opts, _) = optparser.parse_args()

full_path = os.path.abspath(opts.directory)
all_files = set([filename for filename in os.listdir(full_path)])

all_uighur_words = defaultdict(list)

for line in open(full_path + '/' + 'all_lexicons', encoding='utf-8'):
    lexicons = line.strip().split('\t')
    if len(lexicons) == 3:
        # lets process this a little so everything is not trans1, trans2, trans3.
        translations_string = lexicons[2]
        if translations_string.endswith("."):
            translations_string = translations_string[:-1]
        translations_array = [t.strip() for t in translations_string.split(',')]
        translations_array = [t for t in translations_array if len(t) > 0]
        all_uighur_words[lexicons[0]] += translations_array
    else:
        all_uighur_words[lexicons[0]] = []

webcrawl_content = open(full_path + '/' + 'webcrawl_no-en_no-zh.ug', encoding='utf-8').read()

uighur_token_frequency = defaultdict(int)

for token in webcrawl_content.split(' '):
    if token in all_uighur_words.keys():
        uighur_token_frequency[token] += 1

if opts.original_dictionary:
    tab_separated_uighur_and_translation = []
    for line in open(opts.original_dictionary, encoding='utf-8'):
        cells = line.strip().split("\t")
        word = cells[0]
        tab_separated_uighur_and_translation.append("\t".join([word]+list(set(all_uighur_words[word]))))
else:
    tab_separated_uighur_and_translation = [ "\t".join([k]+list(set(all_uighur_words[k]))) for k in uighur_token_frequency.keys()]

with open(full_path + '/dict.ug', 'w', encoding='utf-8') as text_file:
    text_file.write("\n".join(tab_separated_uighur_and_translation))