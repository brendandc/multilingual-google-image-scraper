import optparse
import os

optparser = optparse.OptionParser()
optparser.add_option("-l", "--language", dest="language", default="French", help="Language to package")
optparser.add_option("-d", "--directory", dest="directory", help="Directory with extracted language package")
optparser.add_option("-o", "--output_file", dest="output_file", help="Filename to write the report to")
(opts, _) = optparser.parse_args()

package_directory = opts.directory
if not package_directory.endswith('/'):
    package_directory += '/'

for word_folder_name in os.listdir(package_directory):
    full_word_path = package_directory + word_folder_name
    word = open(full_word_path + '/word.txt', 'r', encoding='utf-8').read().strip()

    for filename in os.listdir(full_word_path):
        if filename.endswith('.txt') or filename.endswith('.json'):
            continue
        full_file_path = full_word_path + '/' + filename

        # size in bytes
        file_size = os.path.getsize(full_file_path)
        print(file_size)
    exit()


    #exit()