import optparse
import os

optparser = optparse.OptionParser()
optparser.add_option("-l", "--language", dest="language", default="French", help="Language to package")
optparser.add_option("-b", "--bucket", dest="bucket", default="brendan.callahan.thesis", help="S3 bucket name")
optparser.add_option("-p", "--prefix", dest="prefix", help="Alternate prefix for the filenames, default is lower case language name")
optparser.add_option("-S", action="store_true", dest="skip_completed_words", help="Allows multiple passes so we can resume if any failures")
(opts, _) = optparser.parse_args()

# TODO: un-hard code the base destination and source paths
BASE_DESTINATION_PATH = '/mnt/storage2/intermediate/'
BASE_SOURCE_PATH = '/mnt/storage/'+opts.language+'/'
BASE_TAR_PATH = BASE_DESTINATION_PATH + opts.language.lower()
file_prefix = opts.prefix or opts.language.lower()
big_tar_file_name = file_prefix+"-package.tar"
sample_tar_file_name = file_prefix+"-sample.tar"
big_tar_path = BASE_DESTINATION_PATH + big_tar_file_name
sample_tar_path = BASE_DESTINATION_PATH + sample_tar_file_name

if not os.path.exists(BASE_DESTINATION_PATH):
    os.makedirs(BASE_DESTINATION_PATH)

if not opts.skip_completed_words:
    tar_cmd = "tar cvf "+ big_tar_path+" --files-from /dev/null"
    os.system(tar_cmd)
    sample_cmd = "tar cvf "+ sample_tar_path+" --files-from /dev/null"
    os.system(sample_cmd)

    os.system("cd " + BASE_SOURCE_PATH + " && tar rf "+big_tar_path+" all_errors.json")

targz_files = []
for folder_name in os.listdir(BASE_SOURCE_PATH):
    print(folder_name)
    targz_file = folder_name + '.tar.gz'
    targz_path = BASE_DESTINATION_PATH + targz_file
    targz_files.append(targz_file)

    # if skip completed words param was passed, and the filepath exists skip this and move onto the next
    # assume there are no incomplete files (that they are cleaned up manually)
    if opts.skip_completed_words and os.path.isfile(targz_path):
        continue

    add_folder_cmd = "cd " + BASE_SOURCE_PATH + " && tar -czf "+targz_path+" "+folder_name

    print(add_folder_cmd)
    os.system(add_folder_cmd)

add_folders_cmd = "cd " + BASE_DESTINATION_PATH + " && tar rf "+big_tar_file_name+" "+" ".join(targz_files)
print(add_folders_cmd)
os.system(add_folders_cmd)

sample_files = sorted(targz_files)[0:100]
add_folders_cmd_sample = "cd " + BASE_DESTINATION_PATH + " && tar rf "+sample_tar_file_name+" "+" ".join(sample_files)
print(add_folders_cmd_sample)
os.system(add_folders_cmd_sample)

os.system("cd " + BASE_DESTINATION_PATH + " && mv " + big_tar_file_name + " ..")
os.system("cd " + BASE_DESTINATION_PATH + " && mv " + sample_tar_file_name + " ..")


# TODO make aws upload optional
package_upload_cmd = "aws s3 cp /mnt/storage2/" + big_tar_file_name + " s3://" + opts.bucket + "/packages/" + \
                     big_tar_file_name

sample_upload_cmd = "aws s3 cp /mnt/storage2/" + sample_tar_file_name + " s3://" + opts.bucket + "/samples/" + \
                    sample_tar_file_name

os.system(package_upload_cmd)
os.system(sample_upload_cmd)


