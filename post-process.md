python create-language-zip.py -l English
sudo mount /dev/xvdf /mnt/storage
sudo chown ubuntu:ubuntu /mnt/storage
sudo mount /dev/xvdg /mnt/storage2
sudo chown ubuntu:ubuntu /mnt/storage2
aws s3 cp /mnt/storage2/english-package.tar s3://brendan.callahan.thesis/packages/english-package.tar
aws s3 cp /mnt/storage2/english-sample.tar s3://brendan.callahan.thesis/samples/english-sample.tar

Get bucket size in bytes `aws s3api list-objects --bucket brendan.callahan --output json --query "[sum(Contents[].Size), length(Contents[])]"`

