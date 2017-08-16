# coding:utf-8
import sys
sys.path.append("..")

import pymysql
import os
import re
from functools import *
from util import *

conn = pymysql.connect(user='root', passwd='esddse000178', db='pku')
cursor = conn.cursor()

# create table
# =========================================================================
cursor.execute("""CREATE TABLE IF NOT EXISTS courses(
				课程中文名          VARCHAR(200),
				课程英文名          VARCHAR(200),
				课程编码            INT,
				课程介绍网址        VARCHAR(200),
				班号                INT,
				课程类型            VARCHAR(10),
				学分                FLOAT(10,5),
				学时                FLOAT(10,5),
				教师                VARCHAR(200),
				人数                INT,
				起止周              VARCHAR(10),
				上课时间            VARCHAR(2000),
				期末考试时间         VARCHAR(20),
				备注                TEXT,
				先修课程             TEXT,
				中文介绍             TEXT,
				英文介绍             TEXT,
				开设学院             VARCHAR(200),
				通选课领域           VARCHAR(10),
				是否为艺术类课程      VARCHAR(10),
				平台课性质            TEXT,
				平台课类型            TEXT,
				授课语言              VARCHAR(20),
				教科书                TEXT,
				参考资料              TEXT,
				教学大纲              TEXT
		)""")

out = cursor.fetchall()
print(out)

# load and process data
# ===================================================================

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
			chinese_name = 'NULL'           # 课程中文名
			english_name = 'NULL'           # 课程英文名
			course_number = 'NULL'          # 课程编码
			course_site = 'NULL'            # 课程介绍网址
			class_number = 'NULL'           # 班号
			course_type = 'NULL'            # 课程类型
			credits = 'NULL'                # 学分
			course_hours = 'NULL'           # 学时
			teacher_name = 'NULL'           # 教师
			students_number = 'NULL'        # 人数
			start_end_week = 'NULL'         # 起止周
			course_time = 'NULL'            # 上课时间
			final_time = 'NULL'             # 期末考试时间
			notes = 'NULL'                  # 备注
			pre_courses = 'NULL'            # 先修课程
			chinese_introduction = 'NULL'   # 中文介绍
			english_introduction = 'NULL'   # 英文介绍
			course_school = 'NULL'          # 开设学院
			area = 'NULL'                   # 通选课领域
			is_art = 'NULL'                 # 是否为艺术类课程
			platform_property = 'NULL'      # 平台课姓朱
			platform_type = 'NULL'          # 平台课类型
			teaching_language = 'NULL'      # 授课语言
			text_books = 'NULL'             # 教科书
			reference = 'NULL'              # 参考资料
			schedual = 'NULL'               # 教学大纲       

			for item in items:
				item = item.strip().split('：')
				if len(item) < 2:
					continue
				
				# clean
				item[1] = item[1].replace('\xa0','').replace('\ue4c7','').replace('\ue011','').replace('\ufffd','').strip()
				
				if item[1] == '':
					continue

				if item[0] == '课程中文名':
					chinese_name = "'" + item[1] + "'"
				elif item[0] == '课程英文名':
					english_name = "'" + item[1].replace("'","''") + "'"
				elif item[0] == '课程编码':
					course_number = "'" + item[1] + "'"
				elif item[0] == '课程介绍网址':
					course_site = "'" + item[1] + "'"
				elif item[0] == '班号':
					class_number = "'" + item[1] + "'"
				elif item[0] == '课程类型':
					course_type = "'" + item[1] + "'"
				elif item[0] == '学分':
					credits = "'" + item[1] + "'"
				elif item[0] == '学时':
					course_hours = "'" + item[1] + "'"
				elif item[0] == '教师':
					teacher_name = "'" + item[1] + "'"
				elif item[0] == '人数':
					students_number = "'" + item[1] + "'"
				elif item[0] == '起始周':
					start_end_week = "'" + item[1] + "'"
				elif item[0] == '上课时间':
					course_time = "'" + generate_course_time(item[1]) + "'"
				elif item[0] == '期末考试时间':
					final_time = "'" + item[1] + "'"
				elif item[0] == '备注':
					notes = "'" + item[1] + "'"
				elif item[0] == '先修课程':
					pre_courses = "'" + item[1] + "'"
				elif item[0] == '中文介绍':
					chinese_introduction = "'" + item[1].replace("'", "''") + "'"
				elif item[0] == '英文介绍':
					english_introduction = "'" + item[1].replace("'", "''") + "'"
				elif item[0] == '开设学院':
					course_school = "'" + item[1] + "'"
				elif item[0] == '通选课领域':
					area = "'" + item[1] + "'"
				elif item[0] == '是否为艺术类课程':
					is_art = "'" + item[1] + "'"
				elif item[0] == '平台课性质':
					platform_property = "'" + item[1] + "'"
				elif item[0] == '平台课类型':
					platform_type = "'" + item[1] + "'"
				elif item[0] == '授课语言':
					teaching_language = "'" + item[1] + "'"
				elif item[0] == '教科书':
					text_books = "'" + item[1].replace("'","''") + "'"
				elif item[0] == '参考资料':
					reference = "'" + item[1].replace("'","''") + "'"
				elif item[0] == '教学大纲':
					schedual = "'" + item[1].replace("'","''") + "'"
				else:
					print (item[0], 'is not in course property!')

			# add to database
			quest = """
				INSERT courses (
					课程中文名,
					课程英文名,
					课程编码,
					课程介绍网址,
					班号,
					课程类型,
					学分,
					学时,
					教师,
					人数,
					起止周,
					上课时间,
					期末考试时间,
					备注,
					先修课程,
					中文介绍,
					英文介绍,
					开设学院,
					通选课领域,
					是否为艺术类课程,
					平台课性质,
					平台课类型,
					授课语言,
					教科书,
					参考资料,
					教学大纲
				) VALUES ("""               \
				+ chinese_name + ","        \
				+ english_name + ","        \
				+ course_number + ","       \
				+ course_site + ","         \
				+ class_number + ","        \
				+ course_type + ","         \
				+ credits + ","             \
				+ course_hours + ","        \
				+ teacher_name + ","        \
				+ students_number + ","     \
				+ start_end_week + ","      \
				+ course_time + ","         \
				+ final_time + ","          \
				+ notes + ","               \
				+ pre_courses + ","         \
				+ chinese_introduction + ","\
				+ english_introduction + ","\
				+ course_school + ","       \
				+ area + ","                \
				+ is_art + ","              \
				+ platform_property + ","   \
				+ platform_type + ","       \
				+ teaching_language + ","   \
				+ text_books + ","          \
				+ reference + ","           \
				+ schedual                  \
				+ ")"

			#print(quest)
			cursor.execute(quest)
			out = cursor.fetchall()
			print(out)

conn.commit()
cursor.close()
conn.close()


