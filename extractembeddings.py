import torch, numpy
import os
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from torch.autograd import Variable 
from PIL import Image
model = models.resnet34(pretrained=True)
layer = model._modules.get('avgpool')
model.eval()
scaler = transforms.Scale((224, 224))
normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
to_tensor = transforms.ToTensor()

def get_vector(image_name):
	img = Image.open(image_name).convert('RGB')
	t_img = Variable(normalize(to_tensor(scaler(img))).unsqueeze(0))
	my_embedding = torch.zeros(1, 512, 1, 1)
	def copy_data(m, i, o):
		my_embedding.copy_(o.data)
	h = layer.register_forward_hook(copy_data)
	model(t_img)
	h.remove()
	return my_embedding

model = models.resnet34(pretrained=True)
layer = model._modules.get('avgpool')
model.eval()
scaler = transforms.Resize((224, 224))
normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
to_tensor = transforms.ToTensor()
for file in os.listdir('testing7/English')[21:]:
    print(file)
    if ("json" not in file):
        l = []
        with open('testing7/English/'+file+'/word.txt') as w:
            word = w.readline().strip().replace(' ', '_')
            print(word)
        for f in os.listdir('testing7/English/'+file):
            if ("json" not in f) and ("txt" not in f):
                try:
                    x = get_vector('testing7/English/'+file+'/'+f).data.numpy()[0, :, 0, 0]
                    l.append(x)
                    with open('100/'+word, 'a') as f:
                        numpy.savetxt(f, x.reshape(1, 512), fmt="%s")
                except:
                    continue
        average = numpy.zeros(512,)
        for embedding in l:
            average += embedding
        average = average / len(l)
        with open('100avg/'+word, 'a') as f:
            numpy.savetxt(f, x.reshape(1, 512), fmt="%s")



		
