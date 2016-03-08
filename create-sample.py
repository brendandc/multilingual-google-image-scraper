import optparse
import os

optparser = optparse.OptionParser()
optparser.add_option("-l", "--language", dest="language", default="French", help="Language to scrape")
optparser.add_option("-d", "--dictionary", dest="dictionary", default="dict.fr", help="Google languages json file")
(opts, _) = optparser.parse_args()
BASE_PATH = '/mnt/storage/'
tar_path = BASE_PATH + opts.language.lower()+"-sample.tar"

english_word_list = [line.strip().split('\t')[1].lower() for line in open(opts.dictionary)]

sorted_english_word_indices = [i[0] for i in sorted(enumerate(english_word_list), key=lambda w: w[1])]

tar_cmd = "tar cvf "+ tar_path+" --files-from /dev/null"
os.system(tar_cmd)
os.system("cd " + BASE_PATH)

for x in sorted_english_word_indices[0:100]:
    add_folder_cmd = "cd " + BASE_PATH + " && tar rf "+tar_path+" "+opts.language+"/"+str(x)
    print(add_folder_cmd)
    os.system(add_folder_cmd)

gzip_cmd = "gzip "+tar_path
os.system(gzip_cmd)