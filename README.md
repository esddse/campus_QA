## 基本信息

### 需要以下依赖包:
	python3 
	pyltp 
 	tensorflow 1.0
 	numpy 
 	whoosh

### 运行方式(暂时):

1. 交互式：使用命令``python3 QAsystem.py``运行
2. 文件式(批量式)：使用命令``python3 QAsystem.py -f <filename>``运行,如``python3 QAsystem.py -f ./data/test_questions``



### 文件结构:

**data**: 包含模型训练以及测试的数据

**ltp_data**：pyltp的模型文件

**papers**：一些论文

**pkuCourseCrawler**：北大dean课程爬虫，java编写

**pkuDatabase**：建立问答系统数据库，包括mysql以及whoosh两种实现，当前用的是whoosh

**qaMatcher**: 问题答案匹配

**questionClassification**：问题分类

**QAsystem.py**: 主程序,定义了主要流程

**util.py**: 一些杂项函数


## TODO 王一雪

### 项目部署在服务器上【**<font color=red>已完成</font>**】

**************************

此部分已完成，**<font color=red >注意以下几点</font>**

* 项目地址在``/home/esddse/campusQA``,复制一份到自己的目录
* 复制后，需要修改模型的记录的路径,如使用qaMatcher的模型，修改``/home/esddse/campusQA/campusQA/qaMatcher/runs/1488501806/checkpoints/checkpoint``里面的路径为当前模型的路径
* 运行前不要忘记打开虚拟环境

**************************

原因：1、PC速度慢、内存小，模型受到限制  2. 编写可视化界面的需求

实验室服务器A需要从内网登录，因此需要一个跳板服务器B，**<font color=red >服务器A、B的账号密码私信我</font>**，具体做法如下：

1、在B上创建目录``mkdir transfer``,这是中转目录，文件可以从本地上传到这里，再用``scp``命令上传到目标服务器A

2、然后在A上原样部署项目，注意以下几点：
* 由于A服务器网速较慢，为了避免上传的麻烦，哈工大LTP的数据、维基语料以及训练完的模型不要上传。哈工大LTP可以参考[博客A](http://blog.csdn.net/churximi/article/details/51174182)。维基语料已经下载好(路径``/home/esddse/campusQA/wiki_data``)，需要重新清洗以及用word2vec产生词向量，具体步骤参考[博客B](http://licstar.net/archives/262)和[博客C](http://www.cnblogs.com/tina-smile/p/5178549.html)
* python3的tensorflow我已装到了一个虚拟环境，运行前使用命令``source /home/esddse/campusQA/env/bin/activate``启动环境，运行之后使用命令``deactivate``退出环境
* 安装的tensorflow版本是1.2，不确定是否能运行，如果不行可以和我说，我看能不能装回原来的版本

### 原来模型的问题

模型的流程是这个样子的：
1. 得到一个问题
2. 通过questionClassifier进行问题分类(简单CNN模型)，得到问题类别，得到之后提取答案的目标属性集合，比如分类的结果是NUMBER，那么答案一定在属性：学时、学分、课程人数等等用数字表示的属性之中
3. 通过词性标注从问题中抽取名词、形容词等作为关键词
4. 抽取候选答案字符串集合，方式如下：对上面每一个关键词，将其作为key，通过whoosh检索，如果一个课程实体的名称包含这个词，提取这个实体的目标属性，然后对每个属性，使用[课程名+属性名+属性值]的方式构造一个“假句子”。比如对关键词“高等”，检索出了“高等数学”这个课程实体，此时步骤2产生的目标属性集合为[“学时”、“学分”、“课程人数”]，分别提取出学时值为32、学分值为2，课程人数值为100，构造“假句子”为[“高等数学学时32”，“高等数学学分2”，“高等数学课程人数100”]。这些假句子的集合就是候选答案字符串
5. 通过qaMatcher（也是CNN模型）对所有候选答案字符串和原问题进行匹配，计算得分，得分最高的即为答案

几个问题：
1. 两个CNN模型对句子的建模是同样的方式，这里出现了很大的重复
2. 两个模型分别训练，最终问答效果在训练的时候是看不出来的。模型分别效果好加起来却并不好
3. 原来由于电脑过于垃圾的问题，CNN模型的词向量我都换成了字向量，速度变快了内存变小了但是效果应该是变差了

### 我的想法

1. 最好弄成一个end to end的模型，直接使用问题-答案对进行训练
2. 替换成词向量
3. 可以尝试attention和RNN的一些模型
3. 可以加入一些句法分析更好地确定提问的对象，我上面的“分词-词性-匹配”的方法并不是一个好的方法
4. 不一定非得是深度学习，传统的方法可以大胆加进去

## TODO 汤济之

### 交互界面

接口的定义

框架选择

### 数据

爬取更多数据

新数据库的建立