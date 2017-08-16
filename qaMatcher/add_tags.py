

lines = []
with open('qa_pairs', 'r', encoding='utf8') as f:
	for line in f:
		line = line.strip()	
		line += ':1'
		lines.append(line)

with open('qa', 'w', encoding='utf8') as f:
	for line in lines:
		f.write(line + '\n')	 