#### 需要以下依赖包:
	python3 
	pyltp 
 	tensorflow 1.0
 	numpy 
 	whoosh

#### 运行方式:
1. 将 util.py 里的 ../ 全部替换为 ./
2. python3 QAsystem.py

#### 文件结构:
###### data: 

包含模型训练以及测试的数据


###### ltp_data： 
pyltp的模型文件
###### papers： 
一些论文
###### pkuCourseCrawler： 
北大dean课程爬虫，java编写
###### pkuDatabase： 
建立问答系统数据库，包括mysql以及whoosh两种实现，当前用的是whoosh
###### qaMatcher: 
问题答案匹配
###### questionClassification：
问题分类
###### QAsystem.py: 
主程序,定义了主要流程
###### util.py: 
一些杂项函数

