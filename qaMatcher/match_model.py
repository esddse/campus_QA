# coding:utf-8

import sys
sys.path.append("..")


from util import *
import tensorflow as tf
import numpy as np

class TestConfig(object):
	# model parameters
	max_sentence_length = 100
	num_classes = 2
	embedding_dim = 300
	filter_sizes = [2,3,4,5,6,7,8,9,10]
	num_filters = 128
	l2_reg_lambda = 0.0
	dropout_keep_prob = 0.5

	# training parameters
	segment_way = 'c'         # way of sentence segmentation, 'c' for character, 'w' for word
	batch_size = 128
	num_epochs = 25           # an epoch runs throughout all the training data
	num_checkpoints = 5       # (batch)
	checkpoint_every = 20     # (batch)
	evalue_every = 100         # (batch)

class NN(object):

	def conv2d_maxpool(self, config, input_x):
		# convolution and max pooling
		pooled_outputs = []
		for filter_size in config.filter_sizes:
			with tf.name_scope("conv-maxpool-%s" % filter_size):
				# convolution
				filter_shape = [filter_size, config.embedding_dim, 1, config.num_filters]
				W = tf.Variable(tf.truncated_normal(filter_shape, stddev=0.1), name="W")
				b = tf.Variable(tf.constant(0.1, shape=[config.num_filters]), name="b")
				x = tf.reshape(input_x, [-1, config.max_sentence_length, config.embedding_dim, 1])
				# conv
				conv = tf.nn.conv2d(x, W, strides=[1,1,1,1], padding="VALID", name="conv")
				# non-linear
				h = tf.nn.relu(tf.nn.bias_add(conv, b), name="relu")
				# max-pool
				pooled = tf.nn.max_pool(h, ksize=[1, config.max_sentence_length-filter_size+1,1,1], \
					strides=[1,1,1,1], padding="VALID", name="pool")
				pooled_outputs.append(pooled)

		# combine all pooled features
		num_filters_total = config.num_filters * len(config.filter_sizes)
		h_pool = tf.concat(axis=3, values=pooled_outputs)
		h_pool_flat = tf.reshape(h_pool, [-1, num_filters_total])

		return h_pool_flat

	def __init__(self, config):

		# parameters
		max_sentence_length = config.max_sentence_length
		num_classes = config.num_classes
		embedding_dim = config.embedding_dim
		filter_sizes = config.filter_sizes
		num_filters = config.num_filters
		l2_reg_lambda = config.l2_reg_lambda
		num_filters_total = num_filters * len(filter_sizes)

		# placeholders for input, output and dropout
		self.input_x_q = tf.placeholder(tf.float32, \
			[None, max_sentence_length, embedding_dim], name="input_x_q")
		self.input_x_a = tf.placeholder(tf.float32, \
			[None, max_sentence_length, embedding_dim], name="input_x_a")
		self.input_y = tf.placeholder(tf.float32, \
			[None, num_classes], name="input_y")
		self.dropout_keep_prob = tf.placeholder(tf.float32, name="dropout_keep_prob")

		# l2 regularization
		l2_loss = tf.constant(0.)

		# convolution and max-pooling
		with tf.name_scope("convolution_question"):
			self.h_pool_flat_q = self.conv2d_maxpool(config, self.input_x_q)
		with tf.name_scope("convolution_answer"):
			self.h_pool_flat_a = self.conv2d_maxpool(config, self.input_x_a)

		# calculate similarity
		with tf.name_scope("simmilarity"):
			M = tf.get_variable("M", shape=[num_filters_total, num_filters_total], \
				initializer=tf.truncated_normal_initializer())
			sim_matrix = tf.matmul(tf.matmul(self.h_pool_flat_q, M,), \
				self.h_pool_flat_a, transpose_b=True)
			self.sim_x = tf.reshape(tf.diag_part(sim_matrix), [-1,1])
	
		# join layer
		with tf.name_scope("join"):
			self.join = tf.concat(axis=1, values=[self.h_pool_flat_q, self.sim_x, self.h_pool_flat_a])

		join_dim = 2 * num_filters_total + 1

		# fully-connexted layer 1
		with tf.name_scope("hidden"):
			W = tf.get_variable("W_hidden", shape=[join_dim, join_dim], \
				initializer=tf.contrib.layers.xavier_initializer())
			b = tf.Variable(tf.constant(0.1, shape=[join_dim]), name="b")
			self.hidden = tf.nn.xw_plus_b(self.join, W, b, name="hidden")

		# dropout
		with tf.name_scope("dropout"):
			self.h_drop = tf.nn.dropout(self.hidden, self.dropout_keep_prob)

		# full-connected layer
		with tf.name_scope("output"):
			W = tf.get_variable("W_output", shape=[join_dim, num_classes], \
				initializer=tf.contrib.layers.xavier_initializer())
			b = tf.Variable(tf.constant(0.1, shape=[num_classes]), name="b")
			l2_loss += tf.nn.l2_loss(W)
			l2_loss += tf.nn.l2_loss(b)
			self.scores = tf.nn.xw_plus_b(self.h_drop, W, b, name="scores")
			self.prob = tf.nn.softmax(self.scores)
			self.prediction = tf.argmax(self.scores, 1, name="predictions")

		# loss: cross-entropy and train
		with tf.name_scope("loss"):
			losses = tf.nn.softmax_cross_entropy_with_logits(logits=self.scores, labels=self.input_y)
			self.loss = tf.reduce_mean(losses) + l2_reg_lambda * l2_loss

		# accuracy
		with tf.name_scope("accuracy"):
			correct_predictions = tf.equal(self.prediction, tf.argmax(self.input_y, axis=1))
			self.accuracy = tf.reduce_mean(tf.cast(correct_predictions, "float"), name="accuracy")



