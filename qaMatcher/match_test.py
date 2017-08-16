# coding:utf-8

import sys
sys.path.append("..")

from util import *
from match_model import *
from match_train import *
import tensorflow as tf
import numpy as np
import time
import datetime
import os

class qaPairMatcher(object):
	# load settings
	def __init__(self, config):
		# config
		self.config = config
		# load word vectors
		word_num, embedding_dim, self.embedding_dict = load_embedding_vectors(self.config.segment_way)
		# load model

	# test strings
	def match_strings(self, questions, answers):

		# run model
		checkpoint_file = tf.train.latest_checkpoint('./qaMatcher/runs/1488501806/checkpoints/')
		

		with tf.Graph().as_default(), tf.Session() as sess:

			# load model
			nn = NN(self.config)
			
			# restore variables
			saver = tf.train.Saver()
			saver.restore(sess, checkpoint_file)

			# generate batches for one epoch
			batches = batch_iter(list(zip(questions, answers)), self.config.batch_size, 1, shuffle=False)

			# collect the probabilities for every batchers
			all_probabilities = []

			for batch in batches:
				x_q_batch, x_a_batch = zip(*batch)
				x_q_batch = lookup_sentences_embedding(\
					x_q_batch, self.embedding_dict, self.config.max_sentence_length, self.config.embedding_dim, self.config.segment_way)
				x_a_batch = lookup_sentences_embedding(\
					x_a_batch, self.embedding_dict, self.config.max_sentence_length, self.config.embedding_dim, self.config.segment_way)
				batch_probabilities = sess.run(nn.prob, feed_dict={
					nn.input_x_q: x_q_batch,
					nn.input_x_a: x_a_batch,
					nn.dropout_keep_prob: 1.
					})
				
				all_probabilities = np.concatenate([all_probabilities, np.concatenate(batch_probabilities[:,:1])])
		
		return all_probabilities


	# test sentences in file: ../data/test_questions
	def match_file(self):

		# load question-answer pairs
		questions, answers = load_test_qa_pairs()

		# run model
		checkpoint_file = tf.train.latest_checkpoint('./runs/1488501806/checkpoints')
		print(checkpoint_file)
		with tf.Graph().as_default(), tf.Session() as sess:
			# load model
			nn = NN(self.config)

			# restore variables
			saver = tf.train.Saver()
			saver.restore(sess, checkpoint_file)

			# generate batches for one epoch
			batches = batch_iter(list(zip(questions, answers)), self.config.batch_size, 1, shuffle=False)

			# collect the probabilities for every batchers
			all_probabilities = []

			for batch in batches:
				x_q_batch, x_a_batch = zip(*batch)
				x_q_batch = lookup_sentences_embedding(\
					x_q_batch, self.embedding_dict, self.config.max_sentence_length, self.config.embedding_dim, self.config.segment_way)
				x_a_batch = lookup_sentences_embedding(\
					x_a_batch, self.embedding_dict, self.config.max_sentence_length, self.config.embedding_dim, self.config.segment_way)
				batch_probabilities = sess.run(nn.prob, feed_dict={
					nn.input_x_q: x_q_batch,
					nn.input_x_a: x_a_batch,
					nn.dropout_keep_prob: 1.
					})
				
				all_probabilities = np.concatenate([all_probabilities, np.concatenate(batch_probabilities[:,:1])])
		
		return all_probabilities
		
def main():
	matcher = qaPairMatcher(TestConfig())
	predictions = matcher.match_file()
	print (predictions)

if __name__ == "__main__":
	main()
