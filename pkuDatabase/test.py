# coding:utf-8

import pymysql

conn = pymysql.connect(user='root', passwd='esddse000178', db='pku')
cursor = conn.cursor()

cursor.execute("select property_name from course_property_type where property_type='Number'")
out = cursor.fetchall()

col = [item[0] for item in out]
quest = "select " + ",".join(col) + " from courses where 课程中文名='电磁学'"
cursor.execute(quest)
out = cursor.fetchall()

print(col)
print(out)

cursor.close()
conn.close()
