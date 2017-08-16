# coding:utf-8

import pymysql

property_dict = {
	'课程中文名':'Definition',
	'课程英文名':'Definition',
	'课程编码':'Number',
	'课程介绍网址':'Location',
	'班号':'Number',
	'课程类型':'Object',
	'学分':'Number',
	'学时':'Number',
	'教师':'Person',
	'人数':'Number',
	'起止周':'Time',
	'上课时间':'Time',
	'期末考试时间':'Time',
	'备注':'Description',
	'先修课程':'Object',
	'中文介绍':'Description',
	'英文介绍':'Description',
	'开设学院':'Organization',
	'通选课领域':'Definition',
	'是否为艺术类课程':'Bool',
	'平台课性质':'Definition',
	'平台课类型':'Definition',
	'授课语言':'Object',
	'教科书':'Object',
	'参考资料':'Object',
	'教学大纲':'Description'
}


conn = pymysql.connect(user='root', passwd='esddse000178', db='pku')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE course_property_type(
		property_name VARCHAR(200),
		property_type VARCHAR(200)
	)''')

for p in property_dict:
	cursor.execute('INSERT course_property_type VALUES ("' + p + '","' + property_dict[p] + '")')

conn.commit()

cursor.close()
conn.close()
