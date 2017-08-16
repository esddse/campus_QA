# coding:utf-8

import numpy as np

data_size = 484608
shuffle_indices = np.random.permutation(np.arange(data_size))


d = {}
i = 0
with open('train_qa_pairs', 'r', encoding='utf8') as f:
	for line in f:
		d[line.strip()] = shuffle_indices[i]
		i += 1

print(i)

d = list(sorted(d.items(), key=lambda item: item[1]))

print(len(d))

with open('train_qa_pairs_shuffled', 'w', encoding='utf8') as f:
	for item in d:
		f.write(item[0] + '\n')