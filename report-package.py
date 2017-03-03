import optparse
import os
import json
import operator
import humanize
from collections import defaultdict
from urllib.parse import urlparse

optparser = optparse.OptionParser()
optparser.add_option("-l", "--language", dest="language", default="French", help="Language to package")
optparser.add_option("-d", "--directory", dest="directory", help="Directory with extracted language package")
optparser.add_option("-o", "--output_file", dest="output_file", help="Filename to write the report to")
optparser.add_option('-i', '--image_limit', type=int, help='Image limit')
(opts, _) = optparser.parse_args()

package_directory = opts.directory
if not package_directory.endswith('/'):
    package_directory += '/'

hostname_counts = defaultdict(int)
extension_counts = defaultdict(int)
total_width = 0
total_height = 0
total_images = 0
total_file_size = 0
total_words = 0
all_word_image_counts = []

VALID_FILE_EXTENSIONS = set(['jpg', 'gif', 'png', 'ico', 'bmp', 'svg'])

for word_folder_name in os.listdir(package_directory):
    if word_folder_name == 'all_errors.json':
        continue
    total_words += 1
    full_word_path = package_directory + word_folder_name
    word = open(full_word_path + '/word.txt', 'r', encoding='utf-8').read().strip()

    try:
        all_metadata = json.load(open(full_word_path + '/metadata.json', 'r', encoding='utf-8'))
    except ValueError:
        print("WARNING: " + full_word_path + " had bad metadata json")
        continue

    # n.b. order by name ascending and omit .txt/.json non-image files
    list_based_files = sorted([f for f in os.listdir(full_word_path) if not f.endswith('.json') and not f.endswith('.txt')])
    num_images_for_this_word = 0

    # n.b. rare case where there was unknown failure and metadata.json was empty but image files exist,
    # print a warning and skip this one for reporting purposes. if 1/10,000 was skipped,
    # not the end of the world
    if len(all_metadata.keys()) == 0 and len(list_based_files) > 0:
        print("WARNING: " + word_folder_name + " had an empty metadata json")
        continue

    for i, filename in enumerate(list_based_files):
        # uses only the top N images if the image limit flag is provided
        if opts.image_limit and i >= opts.image_limit:
            break

        filename_prefix = filename[0:filename.index('.')]
        metadata = all_metadata[filename_prefix]
        success = metadata['success']
        if success:
            num_images_for_this_word += 1

            # n.b. jpg and jpeg are the same thing
            filename_extension = filename[filename.index('.')+1:].lower()
            if filename_extension == 'jpeg':
                filename_extension = 'jpg'
            if filename_extension not in VALID_FILE_EXTENSIONS:
                filename_extension = 'other'

            google_metadata = metadata['google']
            full_file_path = full_word_path + '/' + filename

            # size in bytes
            file_size = os.path.getsize(full_file_path)
            total_file_size += file_size

            try:
                width = google_metadata['ow']
                height = google_metadata['oh']
                total_width += width
                total_height += height
                url = google_metadata['ru']
                net_location = urlparse(url).netloc

                hostname_counts[net_location] += 1
                extension_counts[filename_extension] += 1
            except KeyError:
                print(word_folder_name + ":" + filename_prefix + " failed due to KeyError")

    total_images += num_images_for_this_word
    all_word_image_counts.append(num_images_for_this_word)

sorted_word_image_counts = sorted(all_word_image_counts)

final_report = {
    'total_words': total_words,
    'total_images': total_images,
    'total_file_size': humanize.naturalsize(total_file_size),
    'avg_file_size': humanize.naturalsize(total_file_size / total_images),
    'avg_width': int(total_width / total_images),
    'avg_height': int(total_height / total_images),
    'max_images_per_word': max(all_word_image_counts),
    'min_images_per_word': min(all_word_image_counts),
    'median_images_per_word': sorted_word_image_counts[int(len(sorted_word_image_counts) / 2)],
    'num_unique_hosts': len(hostname_counts.keys()),
    'top_10_hostname_counts': dict(sorted(hostname_counts.items(), key=operator.itemgetter(1), reverse=True)[:10]),
    'extension_counts': extension_counts,
}

json.dump(final_report, open(opts.output_file, 'w', encoding='utf-8'))