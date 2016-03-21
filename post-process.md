python create-language-zip.py -l English
aws s3 cp english-package.tar s3://brendan.callahan/thesis/images/english-package.tar
aws s3 cp english-sample.tar s3://brendan.callahan/thesis/images/english-sample.tar