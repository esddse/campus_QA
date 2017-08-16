# coding:utf-8

import sys
sys.path.append("..")

from optparse import OptionParser

from util import *
from match_model import *
import tensorflow as tf
import numpy as np
import time
import datetime
import os


# generate batches of data for SGD
def batch_iter(data, batch_size, num_epochs, shuffle=True):
	data = np.array(data)
	data_size = len(data)
	num_batches_per_epoch = int((len(data)-1)/batch_size) + 1

	# shuffle the data at each epoch
	if shuffle:
		shuffle_indices = np.random.permutation(np.arange(data_size))
		shuffled_data = data[shuffle_indices]
	else:
		shuffled_data = data
	for batch_num in range(num_batches_per_epoch):
		start_index = batch_num * batch_size
		end_index = min((batch_num + 1) * batch_size, data_size)
		yield shuffled_data[start_index:end_index]


def main():

	# cmd line parameters
	# ===========================================================================

	parser = OptionParser()
	parser.add_option("-m", "--model", dest="model", action="store", type="string", \
		default="test", help="define train model.")
	(options, args) = parser.parse_args()

	config = 0
	if options.model == "test":
		config = TestConfig()
	# default test configuration
	else:
		config = TestConfig()

	

	
	# training
	# ==========================================================================
	
	with tf.Graph().as_default(), tf.Session() as sess:
		nn = NN(config)

		# define training procedure
		global_step = tf.Variable(0, name="global_step", trainable=False)
		optimizer = tf.train.AdamOptimizer(1e-4)
		grads_and_vars = optimizer.compute_gradients(nn.loss)
		train_op = optimizer.apply_gradients(grads_and_vars, global_step=global_step)

		# output directory for models and summaries
		timestamp = str(int(time.time()))
		out_dir = os.path.abspath(os.path.join(os.path.curdir, "runs", timestamp))
		print("writing to {}\n".format(out_dir))

		# summaries for loss and accuracy
		loss_summary = tf.summary.scalar("loss", nn.loss)
		acc_summary = tf.summary.scalar("accuracy", nn.accuracy)

		# train summaries
		train_summary_op = tf.summary.merge([loss_summary, acc_summary])
		train_summary_dir = os.path.join(out_dir, "summaries", "train")
		train_summary_writer = tf.summary.FileWriter(train_summary_dir, sess.graph)

		# dev summaries
		dev_summary_op = tf.summary.merge([loss_summary, acc_summary])
		dev_summary_dir = os.path.join(out_dir, "summaries", "dev")
		dev_summary_writer = tf.summary.FileWriter(dev_summary_dir, sess.graph)

		# checkpoint directory
		checkpoint_dir = os.path.abspath(os.path.join(out_dir, "checkpoints"))
		checkpoint_prefix = os.path.join(checkpoint_dir, "model")
		if not os.path.exists(checkpoint_dir):
			os.makedirs(checkpoint_dir)
		saver = tf.train.Saver(max_to_keep=config.num_checkpoints)

		# initializa all variables
		tf.global_variables_initializer().run()






		def train_step(x_q_batch, x_a_batch, y_batch):
			"""
			single train step
			"""
			_, step, summaries, accuracy = sess.run([train_op, global_step, train_summary_op, nn.accuracy], feed_dict={
				nn.input_x_q: x_q_batch, 
				nn.input_x_a: x_a_batch, 
				nn.input_y: y_batch,
				nn.dropout_keep_prob: config.dropout_keep_prob 
				})
			
			print("trian accuracy = ", accuracy)
			train_summary_writer.add_summary(summaries, step)

		def dev_step(x_q_batch, x_a_batch, y_batch):
			"""
			evaluate model on a dev set
			"""
			_, step, summaries, accuracy = sess.run([train_op, global_step, dev_summary_op, nn.accuracy], feed_dict={ 
				nn.input_x_q: x_q_batch, 
				nn.input_x_a: x_a_batch, 
				nn.input_y: y_batch, 
				nn.dropout_keep_prob: 1. 
				})
			
			print("evalue accuracy = ", accuracy)
			dev_summary_writer.add_summary(summaries, step)





		# load word vectors
		word_num, embedding_dim, embedding_dict = load_embedding_vectors(config.segment_way)
		# load qa pairs
		shuffled_qa_pairs = load_train_qa_pairs_shuffled()

		epoch = 0
		# every epoch train 100000 qa pairs
		for train_questions, train_answers, train_tags in shuffled_qa_pairs:
			epoch += 1
			if epoch == config.num_epochs:
				break

			x_q, x_a, y = np.array(train_questions), np.array(train_answers), np.array(train_tags)

			# random shuffle
			np.random.seed(10)
			shuffle_indices = np.random.permutation(np.arange(len(y)))
			x_q_shuffled = x_q[shuffle_indices]
			x_a_shuffled = x_a[shuffle_indices]
			y_shuffled = y[shuffle_indices]

			# split train/test set, use 10% data to be test set
			split_index = int(0.005 * float(len(y)))  
			x_q_train, x_q_dev = x_q_shuffled[split_index:], x_q_shuffled[:split_index]
			x_a_train, x_a_dev = x_a_shuffled[split_index:], x_a_shuffled[:split_index]
			y_train, y_dev = y_shuffled[split_index:], y_shuffled[:split_index]


			# generate batches
			print("random shuffling...")
			batches = batch_iter(list(zip(x_q_train, x_a_train, y_train)), \
				config.batch_size, config.num_epochs)
			# train for each batch
			print('training...')

			x_q_dev = lookup_sentences_embedding(\
				x_q_dev, embedding_dict, config.max_sentence_length, config.embedding_dim, config.segment_way)
			x_a_dev = lookup_sentences_embedding(\
				x_a_dev, embedding_dict, config.max_sentence_length, config.embedding_dim, config.segment_way)
			y_dev = qa_pairs_tags_2_vectors(y_dev)

			for batch in batches:
				x_q_batch, x_a_batch, y_batch = zip(*batch)
				# embedding sentences, and convert tag to vector
				x_q_batch = lookup_sentences_embedding(\
					x_q_batch, embedding_dict, config.max_sentence_length, config.embedding_dim, config.segment_way)
				x_a_batch = lookup_sentences_embedding(\
					x_a_batch, embedding_dict, config.max_sentence_length, config.embedding_dim, config.segment_way)
				y_batch = qa_pairs_tags_2_vectors(y_batch)
				train_step(x_q_batch, x_a_batch, y_batch)
				current_step = tf.train.global_step(sess, global_step)
				# evalue
				if current_step % config.evalue_every == 0:
					dev_step(x_q_dev, x_a_dev, y_dev)
				# save model 
				if current_step % config.checkpoint_every == 0:
					path = saver.save(sess, checkpoint_prefix, global_step=current_step)

if __name__ == '__main__':
	main()