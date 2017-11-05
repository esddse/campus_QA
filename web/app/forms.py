#coding:utf8

import time
import pymysql
from flask_wtf import Form
from wtforms   import TextField
from wtforms.validators import DataRequired

class QuestionForm(Form):
	question = TextField('question', validators=[DataRequired()])

	
def insert_into_database(question):
	db = pymysql.connect("localhost", "root", "webkdd", "esddse", charset="utf8")
	cursor = db.cursor()

	answers = None

	try:
		question.replace('"', r'\"')
		question.replace("'", r"\'")
		# test if already in database
		cursor.execute("SELECT * from campusQA WHERE question LIKE '%s'" % (question))
		result = cursor.fetchone()
		if result is None or result == '':
			cursor.execute("INSERT INTO campusQA (question) VALUES('%s')" % (question))
			db.commit()
		else:
			answers = result[1]
	except Exception as e:
		db.rollback()
		print(e)

	cursor.close()
	db.close()

	return answers

def get_answer(question):
	db = pymysql.connect("localhost", "root", "webkdd", "esddse", charset="utf8")
	cursor = db.cursor()

	answers = ''

	try:
		question.replace('"', r'\"')
		question.replace("'", r"\'")
		while True:
			print "fetch..."
			cursor.execute("SELECT answer from campusQA WHERE question LIKE '%s' AND is_processed=1" % (question))
			result = cursor.fetchone()
			db.commit()
			print "result: ", result
			if result != '' and result is not None:
				answers = result[0]
				break
			time.sleep(0.1)

	except Exception as e:
		db.rollback()
		print(e)

	cursor.close()
	db.close()

	return answers


