import optparse
import os
import glob

optparser = optparse.OptionParser()
optparser.add_option("-f", "--filename", dest="filename", help="Language package file")
optparser.add_option("-d", "--destination", dest="destination", help="Base destination folder")
optparser.add_option("-l", "--language", dest="language", help="Language to un-package")
(opts, _) = optparser.parse_args()

full_destination_path = opts.destination + "/" + opts.language

if not os.path.exists(full_destination_path):
    os.makedirs(full_destination_path)

outer_untar_command = "tar -xvf " + opts.filename + " -C " + full_destination_path
print(outer_untar_command)
os.system(outer_untar_command)

for inner_filename in glob.glob(full_destination_path+"/*.tar.gz"):
    inner_untar_command = "tar -xvzf " + inner_filename + " -C " + full_destination_path
    print(inner_untar_command)
    os.system(inner_untar_command)
    inner_delete_command = "rm " + inner_filename
    print(inner_delete_command)
    os.system(inner_delete_command)