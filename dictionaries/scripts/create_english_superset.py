import optparse
import os

optparser = optparse.OptionParser()
optparser.add_option("-d", "--directory", dest="directory", default="dictionaries/", help="Directory with dictionaries")
(opts, _) = optparser.parse_args()

full_path = os.path.abspath(opts.directory)

all_english_words = set()
for filename in os.listdir(full_path):
    if filename.startswith('dict'):
        for line in open(full_path+'\\'+filename, encoding='utf-8'):
            translations = line.strip().split('\t')
            foreign_word = translations[0]

            # skip the first word because it is the foreign word
            for word in translations[1:]:
                all_english_words.add(word)

all_english_words_list = list(all_english_words)
words_per_batch = 10000
words_by_batch = [all_english_words_list[i:i+words_per_batch] for i in range(0, len(all_english_words_list), words_per_batch)]

for i, word_batch in enumerate(words_by_batch):
    with open(full_path+'\\english.superset'+"{0:0=2d}".format(i+1), 'w', encoding='utf-8') as text_file:
        text_file.write("\n".join(word_batch))
