# coding:utf8

from pyltp import Segmentor
from whoosh.index import *
from whoosh.fields import *
from whoosh.analysis import RegexAnalyzer
from whoosh.analysis import Tokenizer, Token

import os


##  Some pre-defined tools  ##
print('loading chinese word segmentor pyltp...')
segmentor = Segmentor()
#segmentor.load_with_lexicon('../ltp_data/cws.model', 'course_words')
segmentor.load('../ltp_data/cws.model')


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

# 构建索引
def create_index():

	# create dir
	if not os.path.exists('./courses_whoosh'):
		os.makedirs('./courses_whoosh')

	# create schema and writer
	# ==================================================================

	analyzer = chinese_analyzer()
	schema = Schema(课程中文名=TEXT(stored=True, analyzer=analyzer), \
			        课程英文名=TEXT(stored=True, analyzer=analyzer), \
			        课程编码=ID(stored=True), \
			        课程介绍网址=ID(stored=True), \
			        班号=ID(stored=True), \
			        课程类型=ID(stored=True), \
			        学分=NUMERIC(float, stored=True), \
			        学时=NUMERIC(float, stored=True), \
			        教师=ID(stored=True), \
			        人数=NUMERIC(int, stored=True), \
			        起始周=NUMERIC(int, stored=True), \
			        结束周=NUMERIC(int, stored=True), \
			        上课时间=TEXT(stored=True, analyzer=analyzer), \
			        期末考试时间=TEXT(stored=True, analyzer=analyzer), \
			        备注=TEXT(stored=True, analyzer=analyzer), \
			        先修课程=TEXT(stored=True, analyzer=analyzer), \
			        中文介绍=TEXT(stored=True, analyzer=analyzer), \
			        英文介绍=TEXT(stored=True, analyzer=analyzer), \
			        开设学院=TEXT(stored=True, analyzer=analyzer), \
			        通选课领域=ID(stored=True),\
			        是否为艺术类课程=BOOLEAN(stored=True),\
			        平台课性质=TEXT(stored=True, analyzer=analyzer), \
			        平台课类型=TEXT(stored=True, analyzer=analyzer), \
			        授课语言=TEXT(stored=True, analyzer=analyzer), \
			        教科书=TEXT(stored=True, analyzer=analyzer), \
			        参考资料=TEXT(stored=True, analyzer=analyzer), \
			        教学大纲=TEXT(stored=True, analyzer=analyzer)
			        )
	ix = create_in("./courses_whoosh", schema)
	writer = ix.writer()

	# read data and create index
	# ======================================================================

	courses_root_path = 'courses16-17-2'
	# dir for every school
	schools = os.listdir(courses_root_path)
	for school in schools:
		school_courses_path = os.path.join(courses_root_path, school)
		courses = courses_path = os.listdir(school_courses_path)

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

				writer.add_document(课程中文名=chinese_name, \
					                课程英文名=english_name, \
					                课程编码=course_number, \
					                课程介绍网址=course_site, \
					                班号=class_number, \
					                课程类型=course_type, \
					                学分=credits, \
					                学时=course_hours, \
					                教师=teacher_name, \
					                人数=students_number, \
					                起始周=start_week, \
					                结束周=end_week, \
					                上课时间=course_time, \
					                期末考试时间=final_time, \
					                备注=notes, \
					                先修课程=pre_courses, \
					                中文介绍=chinese_introduction, \
					                英文介绍=english_introduction, \
					                开设学院=course_school, \
					                通选课领域=area, \
					                是否为艺术类课程=is_art, \
					                平台课性质=platform_property, \
					                平台课类型=platform_type, \
					                授课语言=teaching_language, \
					                教科书=text_books, \
					                参考资料=reference, \
					                教学大纲=schedual
					                )
	
	writer.commit()

# 检索
def search(search_str):
	title_list = []
	ix = open_dir("./courses_whoosh")
	searcher = ix.searcher()
	results = searcher.find("课程中文名", search_str)
	for hit in results:
		print(hit['课程中文名'])
		print(hit['教师'])
		print(hit['教科书'])
		print(hit.score)
		title_list.append(hit['课程中文名'])
	return title_list

search('自然语言')