# coding:utf-8

import os
import random
import numpy as np

from pyltp import Segmentor

segmentor = Segmentor()
segmentor.load('../ltp_data/cws.model')

from whoosh.index import *
from whoosh.fields import *
from whoosh.analysis import RegexAnalyzer
from whoosh.analysis import Tokenizer, Token

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

ix = open_dir('./courses_whoosh')
searcher = ix.searcher()

# 上课时间 从01串构建字符串
def generate_course_time(c_time):
	c_time_lst = list(c_time)
	week_days = [0, '一', '二', '三', '四', '五', '六', '日']

	single_time_lst = c_time_lst[:104]
	double_time_lst = c_time_lst[104:]

	double = [0, single_time_lst[13:26], single_time_lst[26:39], \
			     single_time_lst[39:52], single_time_lst[52:65], \
			     single_time_lst[65:78], single_time_lst[78:91], \
		   		 single_time_lst[91:104]]

	single = [0, double_time_lst[13:26], double_time_lst[26:39], \
			     double_time_lst[39:52], double_time_lst[52:65], \
			     double_time_lst[65:78], double_time_lst[78:91], \
			     double_time_lst[91:104]]

	txt = ''
	for i in range(1, 8):
		for j in range(1, 13):
			s = d = False
			if single[i][j] == '1':
				s = True
			if double[i][j] == '1':
				d = True
			if s and d:
				txt += '每周星期'+week_days[i]+'第'+str(j)+'节\n'
			elif s:
				txt += '单周星期'+week_days[i]+'第'+str(j)+'节\n'
			elif d:
				txt += '双周星期'+week_days[i]+'第'+str(j)+'节\n'
	return txt

# load qa template
# ===============================================================================

templates = [line.strip() for line in open('question_templates', 'r', encoding='utf8')]


# load course information and convert to qa pairs
# ===============================================================================

positives = []
negatives = []

courses_root_path = 'courses16-17-2'
# dir for every school
schools = os.listdir(courses_root_path)
for school in schools:
	print(school)
	school_courses_path = os.path.join(courses_root_path, school)
	courses = courses_path = os.listdir(school_courses_path)

	cnt = 0
	for course_path in courses_path:
		with open(os.path.join(courses_root_path, school, course_path), 'r', encoding='utf8') as f:
			context = f.read().strip()
			items = context.split('@')

			# course property
			chinese_name = 'no record.'           # 课程中文名
			english_name = 'no record.'           # 课程英文名
			course_number = 'no record.'          # 课程编码
			course_site = 'no record.'            # 课程介绍网址
			class_number = 'no record.'           # 班号
			course_type = 'no record.'            # 课程类型
			credits = 0                           # 学分
			course_hours = 0                      # 学时
			teacher_name = 'no record.'           # 教师
			students_number = 0                   # 人数
			start_week = 0                        # 起始周
			end_week = 0                          # 结束周
			course_time = 'no record.'            # 上课时间
			final_time = 'no record.'             # 期末考试时间
			notes = 'no record.'                  # 备注
			pre_courses = 'no record.'            # 先修课程
			chinese_introduction = 'no record.'   # 中文介绍
			english_introduction = 'no record.'   # 英文介绍
			course_school = 'no record.'          # 开设学院
			area = 'no record.'                   # 通选课领域
			is_art = 'no record.'                 # 是否为艺术类课程
			platform_property = 'no record.'      # 平台课姓朱
			platform_type = 'no record.'          # 平台课类型
			teaching_language = 'no record.'      # 授课语言
			text_books = 'no record.'             # 教科书
			reference = 'no record.'              # 参考资料
			schedual = 'no record.'               # 教学大纲       

			for item in items:
				item = item.strip().split('：')
				if len(item) < 2:
					continue
				
				# clean
				item[1] = item[1].replace('\xa0','').replace('\ue4c7','').replace('\ue011','').replace('\ufffd','').strip()
			
				if item[1] == '':
					continue

				if item[0] == '课程中文名':
					chinese_name = item[1] 
				elif item[0] == '课程英文名':
					english_name = item[1]
				elif item[0] == '课程编码':
					course_number = item[1] 
				elif item[0] == '课程介绍网址':
					course_site = item[1] 
				elif item[0] == '班号':
					class_number = item[1] 
				elif item[0] == '课程类型':
					course_type = item[1] 
				elif item[0] == '学分':
					credits = float(item[1]) 
				elif item[0] == '学时':
					course_hours = float(item[1]) 
				elif item[0] == '教师':
					teacher_name = item[1] 
				elif item[0] == '人数':
					students_number = int(item[1]) 
				elif item[0] == '起始周':
					start_end_week = item[1].split('-')
					start_week = int(start_end_week[0])
					end_week = int(start_end_week[1]) 
				elif item[0] == '上课时间':
					course_time = generate_course_time(item[1]) 
				elif item[0] == '期末考试时间':
					final_time = item[1] 
				elif item[0] == '备注':
					notes = item[1] 
				elif item[0] == '先修课程':
					pre_courses = item[1] 
				elif item[0] == '中文介绍':
					chinese_introduction = item[1]
				elif item[0] == '英文介绍':
					english_introduction = item[1]
				elif item[0] == '开设学院':
					course_school = item[1] 
				elif item[0] == '通选课领域':
					area = item[1] 
				elif item[0] == '是否为艺术类课程':
					is_art = True if item[1]=='是' else False 
				elif item[0] == '平台课性质':
					platform_property = item[1] 
				elif item[0] == '平台课类型':
					platform_type = item[1] 
				elif item[0] == '授课语言':
					teaching_language = item[1] 
				elif item[0] == '教科书':
					text_books = item[1]
				elif item[0] == '参考资料':
					reference = item[1]
				elif item[0] == '教学大纲':
					schedual = item[1]
				else:
					print (item[0], 'is not in course property!')

			print(chinese_name)
			# convert to qa pairs
			positive = []
			negative = []
			questions = []
			answers = []
			for template in templates:
				template = template.replace('chinese_name', chinese_name)
				template = template.replace('english_name', english_name)
				template = template.replace('course_number', course_number)
				template = template.replace('course_site', course_site)
				template = template.replace('class_number', class_number)
				template = template.replace('course_type', course_type)
				template = template.replace('credits', str(credits))
				template = template.replace('course_hours', str(course_hours))
				template = template.replace('teacher_name', teacher_name)
				template = template.replace('students_number', str(students_number))
				template = template.replace('start_week', str(start_week))
				template = template.replace('end_week', str(end_week))
				template = template.replace('course_time', course_time)
				template = template.replace('final_time', final_time)
				template = template.replace('notes', notes)
				template = template.replace('pre_courses', pre_courses)
				template = template.replace('chinese_introduction', chinese_introduction)
				template = template.replace('english_introduction', english_introduction)
				template = template.replace('course_school', course_school)
				template = template.replace('area', area)
				template = template.replace('is_art', '是'if is_art else '否')
				template = template.replace('platform_property', platform_property)
				template = template.replace('platform_type', platform_type)
				template = template.replace('teaching_language', teaching_language)
				template = template.replace('text_books', text_books)
				template = template.replace('reference', reference)
				template = template.replace('schedual', schedual)
				# positive
				template = template.replace('\n','')
				positive.append(template)
				template = template.split('@@@')
				questions.append(template[0])
				answers.append(template[1])
				# negative
				words = list(segmentor.segment(chinese_name))
				neg_chinese_names = []
				for word in words:
					course_names = [hit['课程中文名'] for hit in searcher.find('课程中文名', word)]
					neg_chinese_names += course_names
				if neg_chinese_names is None:
					continue
				neg_chinese_names = list(set(neg_chinese_names))
				if chinese_name in neg_chinese_names:
					neg_chinese_names.remove(chinese_name)
				for neg_chinese_name in neg_chinese_names:
					neg_answer = template[1].replace(chinese_name, neg_chinese_name)
					negative.append(template[0]+'@@@'+neg_answer)
				
			
			c = i = 0
			for question in questions:
				if i == 1:
					break
				for answer in answers:
					pair = question + '@@@'+ answer
					if pair not in positive:
						negative.append(pair)
						c += 1
						if c == len(positive):
							i = 1
			
			positives += positive
			negatives += negative


negatives_size = len(negatives)
negatives_index = range(negatives_size)
negatives_dict = dict(zip(negatives_index, negatives))
negatives_index = np.array(negatives_index)
shuffle_indices = np.random.permutation(np.arange(negatives_size))
shuffle_negatives_index = negatives_index[shuffle_indices]
negatives_index = list(shuffle_negatives_index[:3*len(positives)])
negatives = [negatives_dict[index] for index in negatives_index]


# tag
for i in range(len(positives)):
	positives[i] += '@@@1'
for i in range(len(negatives)):
	negatives[i] += '@@@0'

qa_pairs = positives + negatives

# write to file
# =============================================================================

with open('qa_pairs', 'w', encoding='utf8') as f:
	for qa_pair in qa_pairs:
		f.write(qa_pair+'\n')
