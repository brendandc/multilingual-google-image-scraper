tar -cvzf french.tar.gz French/
aws s3 cp french.tar.gz s3://brendan.callahan/thesis/images/french.tar.gz
python create-sample.py
aws s3 cp french.tar.gz s3://brendan.callahan/thesis/images/french-sample.tar.gz