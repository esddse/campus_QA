# coding:utf-8

from pyltp import Segmentor
from pyltp import Postagger
import sys
import re

from whoosh.index import *
from whoosh.fields import *
from whoosh.analysis import RegexAnalyzer
from whoosh.analysis import Tokenizer, Token

##  Some pre-defined tools  ##
print('loading some tools...')
segmentor = Segmentor()
#segmentor.load_with_lexicon('./ltp_data/cws.model', './pkuDatabase/course_words')
segmentor.load('./ltp_data/cws.model')
postagger = Postagger()
postagger.load('./ltp_data/pos.model')

# 中文分词解析器
class ChineseTokenizer(Tokenizer):
	def __call__(self, value, positions=False, chars=False, \
		         keeporiginal=True, removestops=True, start_pos=0, start_char=0, \
		         mode='', **kwargs):
		assert isinstance(value, text_type), "%r is not unicode"% value
		t = Token(positions, chars, removestops=removestops, mode=mode, **kwargs)
		list_seg = list(segmentor.segment(value))
		for w in list_seg:
			t.original = t.text = w
			t.boost = 0.5
			if positions:
				t.pos = start_pos + value.find(w)
			if chars:
				t.startchar = start_char + value.find(w)
				t.endchar = start_char + value.find(w) + len(w)
			yield t

def chinese_analyzer():
	return ChineseTokenizer()

# segment sentence and do postag
def segment_postag(sentence):
	words = list(segmentor.segment(sentence))
	postags = postagger.postag(words)
	return zip(words, postags)

# load character vector trained by word2vec (wiki data)
def load_character_vectors():
	print('loading character vectors....')
	with open('./data/character_vectors_300', 'r', encoding='utf8') as f:
		# load basic information
		character_num, embedding_dim = list(map(int ,f.readline().strip().split(' ')))
		
		# load word embedding
		embedding_dict = {}
		cnt = 0.
		tsh = 0.
		for line in f:
			line = line.strip().split(' ')
			character = line[0]
			vector = list(map(float ,line[1:]))
			embedding_dict[character] = vector
			# print out state of loading
			cnt += 1
			if cnt/character_num > tsh:
				print('loading.....  %', cnt/character_num*100)
				tsh += 0.1
		
		return character_num, embedding_dim, embedding_dict	

# function for loading word-vectors trained by word2vec (wiki data)
def load_word_vectors():
	print('loading word vectors....')
	with open('./data/word_vectors_300', 'r', encoding='utf8') as f:
		# load basic information
		word_num, embedding_dim = list(map(int ,f.readline().strip().split(' ')))
		
		# load word embedding
		embedding_dict = {}
		cnt = 0.
		tsh = 0.
		for line in f:
			line = line.strip().split(' ')
			word = line[0]
			vector = list(map(float ,line[1:]))
			embedding_dict[word] = vector
			# print out state of loading
			cnt += 1
			if cnt/word_num > tsh:
				print('loading.....  %', cnt/word_num*100)
				tsh += 0.1
		
		return word_num, embedding_dim, embedding_dict	

def load_embedding_vectors(segment_way):
	if segment_way.lower() == 'c':
		return load_character_vectors()
	elif segment_way.lower() == 'w':
		return load_word_vectors()
	else:
		print('wrong segment_way!')
		sys.exit()

def load_embedding_vectors_debug():
	return 1, 300, {' ':[0.]*300}

# load dict: word <---> index
def load_vocab():
	print('loading vocab....')
	with open('./data/wiki_vocab', 'r', encoding='utf8') as f:
		word2index = {'<UNKNOWN>': 0}
		index2word = {0: '<UNKNOWN>'}
		for line in f:
			line = line.strip().split(' ')
			index, word = int(line[0]), line[1]
			if word not in word2index:
				word2index[word] = index
				index2word[index] = word
		return word2index, index2word


# loading sentences for training model
# tag: Person          0
#      Location        1
#      Organization    2
#      Definition      3
#      Number          4 
#      Time            5
#      Object          6
def load_train_sentences():
	print('loading training sentences....')
	sentences = []
	tags = []
	#max_len = 0
	with open('./data/train_questions', 'r', encoding='utf8') as f:
		for line in f:
			line = line.strip().split(':')
			sentences.append(line[0])
			#if len(line[0]) > max_len:
			#	max_len = len(line[0])
			tags.append(line[1])

	#print('max_len = ', max_len)
	return sentences, tags


def load_test_sentences():
	sentences = []
	with open('./data/test_questions', 'r', encoding='utf8') as f:
		for line in f:
			sentences.append(line.strip())
	return sentences

def load_test_qa_pairs():
	questions = []
	answers = []
	with open('./data/test_qa_pairs', 'r', encoding='utf8') as f:
		for line in f:
			line = line.strip().split('@@@')
			questions.append(line[0])
			answers.append(line[1])
	return questions, answers

def load_train_qa_pairs():
	print('loading training qa pairs.......')
	questions = []
	answers = []
	tags = []
	with open('./data/train_qa_pairs', 'r', encoding='utf8') as f:
		for line in f:
			line = line.strip().split('@@@')
			questions.append(line[0])
			answers.append(line[1])
			tags.append(line[2])

	return questions, answers, tags

def load_train_qa_pairs_shuffled():
	max_size, i = 100000, 0
	questions, answers, tags = [], [], []
	while True:
		with open('./data/train_qa_pairs_shuffled', 'r', encoding='utf8') as f:
			for line in f:
				line = line.strip().split('@@@')
				questions.append(line[0])
				answers.append(line[1])
				tags.append(line[2])
				i += 1
				if i == max_size:
					i = 0
					yield questions, answers, tags
					questions, answers, tags = [], [], []


# convert tags to one-hot vector for sentence classification
def sentences_classification_tags_2_vectors(tags):
	tag_index = {'Person':0, 'Location':1, 'Organization':2, 'Definition':3, 'Number':4, 'Time':5, 'Object':6 }
	vectors = []
	for tag in tags:
		tag_vector = [0] * 7
		tag_vector[tag_index[tag]] = 1
		vectors.append(tag_vector)
	return vectors

# convert tags to one-hot vector for matching qa pairs
def qa_pairs_tags_2_vectors(tags):
	return [[1,0] if tag == '1' else [0,1] for tag in tags]


# convert numbers to tags
def num_2_tag(num_list):
	num_index = {0:'Person', 1:'Location', 2:'Organization', 3:'Definition', 4:'Number', 5:'Time', 6:'Object'}
	return [num_index[num] for num in num_list]

# convert sentence to a unified style
def pre_process_sentence(sentence):
	sentence = sentence.replace(' ','').lower()
	sentence = re.sub(r'[()!?（）\[\]{}！？。,\.,&%$#@\\/、:：《》<>]','',sentence)
	return sentence

# padding sentence to maximu length or truncating to maximum length
def sentence_processing(sentence_segment, max_sentence_length):
	sentence_length = len(sentence_segment)
	if sentence_length < max_sentence_length:
		sentence_segment += ["<PAD>"] * (max_sentence_length - sentence_length)
	elif sentence_length > max_sentence_length:
		sentence_segment = sentence_segment[:max_sentence_length]
	return sentence_segment

# give a sentence, return a sentence embedding
def lookup_sentence_embedding_character(sentence, embedding_dict, max_sentence_length, embedding_dim):
	words = list(sentence)
	words = sentence_processing(words, max_sentence_length)
	sentence_embedding = []
	for word in words:
		if word in embedding_dict:
			sentence_embedding.append(embedding_dict[word])
		else:
			sentence_embedding.append([0.] * embedding_dim)
	return sentence_embedding

# give a sentence, return a sentence embedding
def lookup_sentence_embedding_word(sentence, embedding_dict, max_sentence_length, embedding_dim):
	words = list(segmentor.segment(sentence))
	words = sentence_padding(words, max_sentence_length)
	sentence_embedding = []
	for word in words:
		if word in embedding_dict:
			sentence_embedding.append(embedding_dict[word])
		else:
			sentence_embedding.append([0.] * embedding_dim)
	return sentence_embedding

# give a set of sentences, return all the embeddings
# @para segment_way: granularity of segmentation, 'c'(character) or 'w'(word)
def lookup_sentences_embedding(sentences, embedding_dict, max_sentence_length, embedding_dim, segment_way):
	sentence_embeddings = []
	if segment_way.lower() == 'c':
		for sentence in sentences:
			sentence_embeddings.append(lookup_sentence_embedding_character(sentence, \
				embedding_dict, max_sentence_length, embedding_dim))
	elif segment_way.lower() == 'w':
		for sentence in sentences:
			sentence_embeddings.append(lookup_sentence_embedding_word(sentence, \
				embedding_dict, max_sentence_length, embedding_dim))
	else:
		print('wrong segment_way!')
		sys.exit()


	return sentence_embeddings


def main():
	s = "()!?（）[]\{\}！？。,.,&%$#@"
	print(pre_process_sentence(s))


if __name__ == '__main__':
	main()