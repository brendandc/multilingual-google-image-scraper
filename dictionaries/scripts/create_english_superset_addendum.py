import optparse
import os

optparser = optparse.OptionParser()
optparser.add_option("-n", "--new_files", dest="new_files", default="", help="Comma separated list of new files")
optparser.add_option("-d", "--directory", dest="directory", default="dictionaries/", help="Directory with dictionaries")
optparser.add_option("-i", "--start_suffix", dest="start_suffix", type=int, help="Start suffix, i.e. the last suffix + 1")
(opts, _) = optparser.parse_args()

full_path = os.path.abspath(opts.directory)

new_filenames = opts.new_files.split(',')

existing_english_words = set()
for filename in os.listdir(full_path):
    if filename.startswith('dict') and not filename in new_filenames:
        for line in open(full_path+'/'+filename, encoding='utf-8'):
            translations = line.strip().split('\t')
            foreign_word = translations[0]

            # skip the first word because it is the foreign word
            for word in translations[1:]:
                existing_english_words.add(word)

new_english_words = set()
for filename in new_filenames:
    for line in open(full_path + '/' + filename, encoding='utf-8'):
        translations = line.strip().split('\t')
        foreign_word = translations[0]

        # skip the first word because it is the foreign word
        for word in translations[1:]:
            if word not in existing_english_words:
                new_english_words.add(word)

all_english_words_list = list(new_english_words)

words_per_batch = 10000
words_by_batch = [all_english_words_list[i:i+words_per_batch] for i in range(0, len(all_english_words_list), words_per_batch)]

start_suffix = opts.start_suffix or 0

for i, word_batch in enumerate(words_by_batch):
    with open(full_path+'/english.superset'+"{0:0=2d}".format(start_suffix+i), 'w', encoding='utf-8') as text_file:
        text_file.write("\n".join(word_batch))
