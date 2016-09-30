import optparse

optparser = optparse.OptionParser()
optparser.add_option("-f", "--foreign_dictionary", dest="foreign_dict_file", help="Foreign dictionary file")
optparser.add_option("-e", "--english_dictionary", dest="english_dict_file", help="English dictionary file")
(opts, _) = optparser.parse_args()

foreign_dict_filename = opts.foreign_dict_file

all_english_words_mapped = {}
for line in open(opts.foreign_dict_file, encoding='utf-8'):
    translations = line.strip().split('\t')
    foreign_word = translations[0]

    # skip the first word because it is the foreign word
    for word in translations[1:]:
        all_english_words_mapped[word] = foreign_word

all_french_word_translations_present = []
for line in open(opts.english_dict_file, encoding='utf-8'):
    translations = line.strip().split('\t')
    english_word = translations[0]
    if english_word in all_english_words_mapped:
        all_french_word_translations_present.append([english_word, all_english_words_mapped[english_word]])

for english, french in all_french_word_translations_present:
    print("English:"+english + " French:" + french)
