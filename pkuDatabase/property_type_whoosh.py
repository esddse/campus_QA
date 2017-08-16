# coding:utf-8

from whoosh.index import *
from whoosh.fields import *
from whoosh.analysis import RegexAnalyzer
from whoosh.analysis import Tokenizer, Token

import os

if not os.path.exists('./property_type_whoosh'):
	os.makedirs('./property_type_whoosh')

schema = Schema(type=ID(stored=True),
	            property=KEYWORD(stored=True))
ix = create_in("./property_type_whoosh", schema)
writer = ix.writer()

writer.add_document(type="Person", property="教师")
writer.add_document(type="Number", property="课程编码 班号 学分 学时 人数")
writer.add_document(type="Time", property="起始周 结束周 上课时间 期末考试时间")
writer.add_document(type="Organization", property="开设学院")
writer.add_document(type="Object", property="课程类型 先修课程 授课语言 教科书 参考资料")
writer.add_document(type="Location", property="课程介绍网址")
writer.add_document(type="Definition", property="课程中文名 课程英文名 平台课性质 平台课类型")
writer.add_document(type="Bool", property="是否为艺术类课程")
writer.add_document(type="Description", property="中文介绍 英文介绍 教学大纲")

writer.commit()


searcher = ix.searcher()
results = searcher.find("property", "班号")
for hit in results:
	print(hit['type'])