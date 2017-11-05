

from flask import render_template, flash, redirect, request, jsonify
from app   import app
from forms import QuestionForm, insert_into_database, get_answer

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
	form = QuestionForm()

	# if got question
	if request.method == "POST":
		question = request.form['question']
		answers = insert_into_database(question)
		if answers is None or answers == '':
			answers = get_answer(question)
		answers = answers.split('\n\n')
		answers = list(map(lambda answer: answer.split('\t'), answers))
		answers = list(filter(lambda answer: len(answer) == 2, answers))
		for i in range(len(answers)):
			answers[i][0] = answers[i][0].strip()   # answer
			answers[i][1] = answers[i][1].strip()   # score
		return jsonify(answer=answers)
	# question not entered
	else:
		return render_template('index.html', form=form)


