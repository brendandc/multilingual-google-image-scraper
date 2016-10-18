import optparse
import os
import json
from collections import defaultdict
from urllib.parse import urlparse

optparser = optparse.OptionParser()
optparser.add_option("-l", "--language", dest="language", default="French", help="Language to package")
optparser.add_option("-d", "--directory", dest="directory", help="Directory with extracted language package")
optparser.add_option("-o", "--output_file", dest="output_file", help="Filename to write the report to")
(opts, _) = optparser.parse_args()

package_directory = opts.directory
if not package_directory.endswith('/'):
    package_directory += '/'

hostname_counts = defaultdict(int)
extension_counts = defaultdict(int)
total_pixels = 0
total_files = 0
total_file_size = 0

for word_folder_name in os.listdir(package_directory):
    if word_folder_name == 'all_errors.json':
        continue
    full_word_path = package_directory + word_folder_name
    word = open(full_word_path + '/word.txt', 'r', encoding='utf-8').read().strip()
    all_metadata = json.load(open(full_word_path + '/metadata.json', 'r', encoding='utf-8'))
    list_based_files = [f for f in os.listdir(full_word_path) if not f.endswith('.json') and not f.endswith('.txt')]

    for filename in list_based_files:
        filename_prefix = filename[0:filename.index('.')]
        metadata = all_metadata[filename_prefix]
        success = metadata['success']
        if success:
            total_files += 1
            google_metadata = metadata['google']
            full_file_path = full_word_path + '/' + filename

            # size in bytes
            file_size = os.path.getsize(full_file_path)
            total_file_size += file_size

            #FIXME: total gibberish
            type_from_google = google_metadata['ity']

            width = google_metadata['ow']
            height = google_metadata['oh']
            num_pixels = width * height
            total_pixels += num_pixels
            url = google_metadata['ru']
            net_location = urlparse(url).netloc

            hostname_counts[net_location] += 1
            extension_counts[type_from_google] += 1

final_report = {
    'total_files': total_files,
    'total_file_size': total_file_size, #FIXME: make human readable
    'total_pixels': total_pixels,
    'avg_file_size': total_file_size / total_files, #FIXME: make human readable
    'avg_pixels': total_pixels / total_files,
    'hostname_counts': hostname_counts, #FIXME: trim to top N or above a threshold?
    'extension_counts': extension_counts,
}

json.dump(final_report, open(opts.output_file, 'w', encoding='utf-8'))