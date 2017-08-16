# coding:utf-8

import sys
sys.path.append("..")

from util import *
from sentence_classification_model import *
from sentence_classification_train import *
import tensorflow as tf
import numpy as np
import time
import datetime
import os

class sentenceClassifier(object):
	# load settings
	def __init__(self, config):
		# config
		self.config = config
		# load word vectors
		word_num, embedding_dim, self.embedding_dict = load_embedding_vectors(self.config.segment_way)
		# load model

	# test single sentence
	def classify_str(self, sentence):
		# run model
		checkpoint_file = tf.train.latest_checkpoint('./questionClassifier/runs/1488337111/checkpoints')
		with tf.Graph().as_default(), tf.Session() as sess:
			# load model
			cnn = CNN(self.config)

			# restore variables
			saver = tf.train.Saver()
			saver.restore(sess, checkpoint_file)

			
			x = lookup_sentences_embedding(\
				[sentence], self.embedding_dict, self.config.max_sentence_length, self.config.embedding_dim, self.config.segment_way)
			prediction = sess.run(cnn.prediction, feed_dict={
				cnn.input_x: x,
				cnn.dropout_keep_prob: 1.
				})

		return num_2_tag(prediction)[0]		


	# test sentences in file: ../data/test_questions
	def classify_file(self):

		# load sentences
		sentences = load_test_sentences()

		# run model
		checkpoint_file = tf.train.latest_checkpoint('./runs/1488337111/checkpoints')
		print(checkpoint_file)
		with tf.Graph().as_default(), tf.Session() as sess:
			# load model
			cnn = CNN(self.config)

			# restore variables
			saver = tf.train.Saver()
			saver.restore(sess, checkpoint_file)

			# generate batches for one epoch
			batches = batch_iter(list(sentences), self.config.batch_size, 1, shuffle=False)

			# collect the predictions for every batchers
			all_predictions = []

			for x_batch in batches:
				x_batch = lookup_sentences_embedding(\
					x_batch, self.embedding_dict, self.config.max_sentence_length, self.config.embedding_dim, self.config.segment_way)
				batch_predictions = sess.run(cnn.prediction, feed_dict={
					cnn.input_x: x_batch,
					cnn.dropout_keep_prob: 1.
					})
				all_predictions = np.concatenate([all_predictions, batch_predictions])
		
		return num_2_tag(all_predictions)
		
def main():
	classifier = sentenceClassifier(TestConfig())
	predictions = classifier.classify_file()
	print (predictions)

if __name__ == "__main__":
	main()
