# coding:utf-8

import sys
sys.path.append("./questionClassifier")
sys.path.append("./qaMatcher")

from util import *
from sentence_classification_test import *
from match_test import *
import sentence_classification_model as SCM
import match_model as MM

import numpy as np
from optparse import OptionParser

class QuestionAnsweringSystem(object):
	
	def __init__(self):
		# questions classifier
		self.classifier = sentenceClassifier(SCM.TestConfig())
		# matcher to match question and candidate answers
		self.matcher = qaPairMatcher(MM.TestConfig())

		# database search engine
		self.ix_courses = open_dir("./pkuDatabase/courses_whoosh")
		self.ix_property = open_dir("./pkuDatabase/property_type_whoosh")
		self.searcher_courses = self.ix_courses.searcher()
		self.searcher_property = self.ix_property.searcher()

	# 回答一个问题
	def answer_question(self, question):
		question_type = self.classifier.classify_str(question)

		# find target properties
		properties = [hit['property'] for hit in self.searcher_property.find("type", question_type)][0].split(' ')
		print('classify: ', properties)

		# extract entities from question
		postags = segment_postag(question)		
		entities_name = []
		for word, tag in postags:
			if tag.startswith('n') or tag.startswith('a') or tag.startswith('b') or tag.startswith('i'):
				entities_name.append(word)
		print('extract entities: ', entities_name)

		# genetate candidate answer string
		candidate_answers = []
		for entity_name in entities_name:
			# search entity in courses
			course_entities = self.searcher_courses.find("课程中文名", entity_name)
			for course_entity in course_entities:
				for property_ in properties:
					answer = course_entity[property_]
					if answer is not None:
						answer_string = course_entity['课程中文名'] + property_ + str(answer)
						if [answer_string, answer] not in candidate_answers:
							candidate_answers.append([answer_string, answer])

		if len(candidate_answers) == 0:
			return None

		questions = [question] * len(candidate_answers)
		print([candidate_answer[0] for candidate_answer in candidate_answers])
		probabilities = self.matcher.match_strings(questions, [candidate_answer[0] for candidate_answer in candidate_answers])
		results = list(zip([candidate_answer[1] for candidate_answer in candidate_answers], probabilities))
		sorted_results = sorted(results, key=lambda item: item[1], reverse=True)

		for result in sorted_results:
			print(result[0],' ',result[1])

		return sorted_results[0][0]



	# 回答一列表的问题,并输出
	def answer_questions(self, questions, write_to_file=False):
		answers = []
		for question in questions:
			asnwer = self.answer_question(question)
			answers.append(asnwer)
		if write_to_file:
			with open('./data/test_answers', 'w', encoding='utf8') as f:
				for asnwer in answers:
					f.write(answer+'\n')
			print('all answers are writen to file: ./data/test_answers')
		else:
			for question, answer in zip(questions, answers):
				print(question, '\n答:', answer)


def main():
	# define cmd line parameter
	parser = OptionParser()
	parser.add_option("-f", "--file",
		              action="store",
		              type="string",
		              dest="filepath",
		              help="path of input file, the file should contain questions only")
	(options, args) = parser.parse_args()

	# qa system
	question_answering_system = QuestionAnsweringSystem()

	# read questions from file or from cmd line
	if options.filepath is None:
		while True:
			print ('please type in you question (in Chinese), "exit" or "quit" to exit this program:')
			question = input()
			if question == 'exit' or question == 'quit':
				break
			elif question == '':
				continue
			question_answering_system.answer_questions([question])
	else:
		with open(options.filepath, 'r', encoding='utf8') as f:		
			questions = [line.strip() for line in f]
			question_answering_system.answer_questions(questions, write_to_file=True)


if __name__ == '__main__':
	main()