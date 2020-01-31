l = ["red", "orange", "yellow", "green", "blue", "purple"]
for line in open('hundredNouns', 'r'):
	w1 = line.split()[0]
	with open("testDict.txt", 'a') as f:
		f.write("{}\n".format(w1))
	print(w1)
	for w in l:
		with open("testDict.txt", 'a') as f:
			f.write("{} {}\n".format(w, w1))
		print("{} {}".format(w, w1))
