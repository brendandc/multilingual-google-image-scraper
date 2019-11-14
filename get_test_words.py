nouns = []
d = [] 
for line in open('renodata', 'r'):
	line = line.split('\t')
	if (line[2].strip()  == "NN"):
		nouns.append(line[0].strip())
for line in open('Concreteness_ratings_Brysbaert_et_al_BRM.txt', 'r'):
	line = line.split('\t')
	if (line[0].strip() in nouns):
		#d[float(line[2].strip())] = line[0].strip()
		d.append((float(line[2].strip()), line[0]))
for k, v in sorted(d):
	with open('noun_concreteness.txt', 'a') as f:
		f.write("{}\t{}\n".format(v, k))

