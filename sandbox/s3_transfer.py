import boto3

#  when S3 mode is turned on, upload the file over to S3 and delete the local copy
# TODO can we simplify this so it doesn't need to write out to a tmp location?
# TODO add metadata like original link to storage?
# S3_BUCKET_NAME = 'brendan.callahan'
# S3_BASE_PATH = 'thesis/images/'+opts.language+'/'
# if STORAGE_MODE == 'S3':
#     word_index_str = "{0:0=2d}".format(word_index)
#     destination_path = S3_BASE_PATH+word_index_str+'/'+actual_file_name
#     s3_client = boto3.resource('s3')
#     s3_client.meta.client.upload_file(full_path, S3_BUCKET_NAME, destination_path)
#     os.remove(full_path)