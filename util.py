# coding:utf-8

import os
import re
import sys
import threading
from pyltp import Segmentor

cur_path = os.path.dirname(os.path.abspath(__file__)) + '/'

import jieba

segmentor = Segmentor()
segmentor.load(cur_path + 'ltp_data/cws.model')


def load_stop_words():
    cur_path = os.path.dirname(os.path.abspath(__file__)) + '/'
    stop_words = []
    with open(cur_path + 'data/stop_words', 'r', encoding="utf8") as f:
        for line in f:
            stop_words.append(line.strip())
    return stop_words


# 疑问词 “什么” 等
def load_question_words():
    cur_path = os.path.dirname(os.path.abspath(__file__)) + '/'
    question_words = {}
    with open(cur_path + 'data/specific/question_words', 'r', encoding="utf8") as f:
        for line in f:
            word = line.strip()
            if word == "什么" or word == "啥":
                question_words[word] = ""
            elif word == "多少" or word == "几":
                question_words[word] = ""
            elif word == "谁":
                question_words[word] = ""
            elif word == "哪个":
                question_words[word] = ""
            elif word == "哪" or word == "哪里" or word == "哪儿": 
                question_words[word] = "地点"
    return question_words

# 院系完整中文名
def load_school_name():
    cur_path = os.path.dirname(os.path.abspath(__file__)) + '/'
    with open(cur_path + 'data/specific/school/chinese_name', 'r', encoding="utf8") as f:
        lst = []
        for line in f:
            line = line.strip().split('\t')
            entity_id = line[0]
            name      = list(segmentor.segment(line[1]))
            lst.append((entity_id, name))
        return lst

# 院系简称
def load_school_short():
    cur_path = os.path.dirname(os.path.abspath(__file__)) + '/'
    with open(cur_path + 'data/specific/school/chinese_short', 'r', encoding="utf8") as f:
        lst = []
        for line in f:
            line = line.strip().split('\t')
            entity_id = line[0]
            name      = [line[1]]
            lst.append((entity_id, name))
        return lst

# 教师名称
def load_teacher_name():
    cur_path = os.path.dirname(os.path.abspath(__file__)) + '/'
    with open(cur_path + 'data/specific/teacher/name', 'r', encoding="utf8") as f:
        lst = []
        for line in f:
            line = line.strip().split('\t')
            entity_id = line[0]
            name      = [line[1]]
            lst.append((entity_id, name))
        return lst

# 课程名称    
def load_course_name():
    cur_path = os.path.dirname(os.path.abspath(__file__)) + '/'
    with open(cur_path + 'data/specific/course/chinese_name', 'r', encoding="utf8") as f:
        lst = []
        for line in f:
            line = line.strip().split('\t')
            entity_id = line[0]
            name      = list(segmentor.segment(line[1]))
            lst.append((entity_id, name))
        return lst

# 课程简称
def load_course_short():
    cur_path = os.path.dirname(os.path.abspath(__file__)) + '/'
    with open(cur_path + 'data/specific/course/chinese_short', 'r', encoding="utf8") as f:
        lst = []
        for line in f:
            line = line.strip().split('\t')
            entity_id = line[0]
            name      = [line[1]]
            lst.append((entity_id, name))
        return lst


# function for loading word-vectors trained by word2vec (wiki data)
def load_word_vectors():
    print('loading word vectors....')
    with open('./data/word_vectors_300', 'r', encoding='utf8') as f:
        # load basic information
        word_num, embedding_dim = list(map(int ,f.readline().strip().split(' ')))
        
        # load word embedding
        embedding_dict = {}
        cnt = 0.
        tsh = 0.
        for line in f:
            line = line.strip().split(' ')
            word = line[0]
            vector = list(map(float ,line[1:]))
            embedding_dict[word] = vector
            # print out state of loading
            cnt += 1
            if cnt/word_num > tsh:
                print('loading.....  %', cnt/word_num*100)
                tsh += 0.1
        
        return word_num, embedding_dim, embedding_dict  

# check whether 2 strings have characher in common
def is_string_overlap(str1, str2):
    for character in str1:
        if character in str2:
            return True
    return False

# 过滤以及一些规范化
def str_filter(str):
    number_cvt_1 = {'10':'十',
                    '11':'十一',
                    '12':'十二',
                    '13':'十三',
                    '14':'十四',
                    '15':'十五',
                    '16':'十六',
                    '17':'十七',
                    '18':'十八',
                    '19':'十九',
                    '20':'二十'}
    number_cvt_2 = {'1':'一',
                    '2':'二',
                    '3':'三',
                    '4':'四',
                    '5':'五',
                    '6':'六',
                    '7':'七',
                    '8':'八',
                    '9':'九'}
    number_cvt_3 = {'III':'三',
                    'II':'二',
                    'I':'一',
                    'iii':'三',
                    'ii':'二',
                    'i':'一'}
    number_cvt_4 = {'Ⅲ':'三',
                    'Ⅱ':'二',
                    'Ⅰ':'一'}
    
    # replace
    for pattern, repl in number_cvt_1.items():
        str = str.replace(pattern, repl)
    for pattern, repl in number_cvt_2.items():
        str = str.replace(pattern, repl)
    for pattern, repl in number_cvt_3.items():
        str = str.replace(pattern, repl)
    for pattern, repl in number_cvt_4.items():
        str = str.replace(pattern, repl)
    return str

def main():
    def f(x,y): return x+y

    t = ThreadWrapper(f, (1,2))
    print(t.return_value)

if __name__ == "__main__":
    main()