import optparse
import os
from collections import defaultdict

optparser = optparse.OptionParser()
optparser.add_option("-d", "--directory", dest="directory", default="uighur/", help="Directory with dictionaries")
(opts, _) = optparser.parse_args()

full_path = os.path.abspath(opts.directory)
all_files = set([filename for filename in os.listdir(full_path)])

all_uighur_words = set([])

for line in open(full_path + '/' + 'all_lexicons', encoding='utf-8'):
    lexicons = line.strip().split('\t')
    all_uighur_words.add(lexicons[0])

webcrawl_content = open(full_path + '/' + 'webcrawl_no-en_no-zh.ug', encoding='utf-8').read()

uighur_token_frequency = defaultdict(int)

for token in webcrawl_content.split(' '):
    if token in all_uighur_words:
        uighur_token_frequency[token] += 1

with open(full_path + '/dict.ug', 'w', encoding='utf-8') as text_file:
    text_file.write("\n".join(uighur_token_frequency.keys()))