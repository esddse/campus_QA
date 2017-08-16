# coding:utf-8

from pyltp import Segmentor
from pyltp import Postagger
from pyltp import NamedEntityRecognizer

segmentor = Segmentor()
segmentor.load('./ltp_data/cws.model')
postagger = Postagger()
postagger.load('./ltp_data/pos.model')
namedentityrecognizer = NamedEntityRecognizer()
namedentityrecognizer.load('./ltp_data/ner.model')

sentence = "电磁学的老师是谁"
words = segmentor.segment(sentence)
pos = postagger.postag(words)
netags = namedentityrecognizer.recognize(words, pos)

print (' '.join(words))
print (' '.join(pos))
print (' '.join(netags))