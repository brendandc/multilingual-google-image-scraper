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

                # skip if word had no translation
                if foreign_word != word:
                    all_english_words.add(word)

with open(full_path+'\\english.superset', 'w', encoding='utf-8') as text_file:
    text_file.write("\n".join(all_english_words))
