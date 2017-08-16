# coding:utf-8
import sys
sys.path.append("..")

import os
import re
from util import *


def num_2_character(s):
	s = s.replace('1','一')
	s = s.replace('2','二')
	s = s.replace('3','三')
	s = s.replace('4','四')
	s = s.replace('5','五')
	s = s.replace('6','六')
	s = s.replace('7','七')
	s = s.replace('8','八')
	return s

courses_root_path = 'courses16-17-2'

words = []

# dir for every school
schools = os.listdir(courses_root_path)
words += schools

for school in schools:
	school_courses_path = os.path.join(courses_root_path, school)
	courses = courses_path = os.listdir(school_courses_path)
	courses = [re.sub(r'\(\d+\)', '', course) for course in courses]
	courses = list(map(pre_process_sentence, courses))
	courses = [re.sub(r'iii$'  , '三', course) for course in courses]
	courses = [re.sub(r'ii$'   , '二', course) for course in courses]
	courses = [re.sub(r'i$'    , '一', course) for course in courses]
	courses = [re.sub(r'ⅱⅱⅱ$', '三', course) for course in courses]
	courses = [re.sub(r'ⅱⅱ$'  , '二', course) for course in courses]
	courses = [re.sub(r'ⅱ$'    , '一', course) for course in courses]
	courses = list(map(num_2_character, courses))
	courses = list(set(courses))  # unique
	words += courses

	for course_path in courses_path:
		with open(os.path.join(courses_root_path, school, course_path), 'r', encoding='utf8') as f:
			context = f.read().strip()
			items = context.split('@')
			for item in items:
				item = item.strip().split('：')
				#print(item)
				words.append(item[0].strip())
				if item[0] == '教师':
					words.append(item[1].strip())

words = list(set(words))
for word in words:
	print(word)
	