python create-language-zip.py -l English
aws s3 cp french.tar.gz s3://brendan.callahan/thesis/images/English-package.tar.gz
aws s3 cp french.tar.gz s3://brendan.callahan/thesis/images/English-sample.tar.gz