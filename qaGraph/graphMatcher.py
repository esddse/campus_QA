# coding: utf-8

'''
这个模块和匹配有关系
'''

import os
import sys
import re

sys.path.append('.')
sys.path.append('..')

import jieba

from py2neo import authenticate
from py2neo import Graph, Node, Relationship

from util import load_school_name, load_school_short
from util import load_teacher_name
from util import load_course_name, load_course_short


from util import load_stop_words, load_word_vectors, is_string_overlap, str_filter

epsilon = 10e-30

stop_words = load_stop_words()

# ---------------- 图中 ------------------------
# ----------------------------------------------

# 由于表示图中的实体
# 或者是属性（property）
class Entity(object):
    def __init__(self, entity_id, entity_relation, label, property_key, property_value):
        self.entity_id       = entity_id         # 数据库中的结点id
        self.entity_relation = entity_relation   # 关系，这个关系依赖于
        self.label           = label             # 实体标签 课程， 院系 或者 PERSON， 若是properoty 用 label='property'的对象代替
        self.property_key    = property_key      # 属性key
        self.property_value  = property_value    # 属性value

        self.cnt = 0.   # 计数，用于倒排索引预匹配

    def print(self):
        print([self.entity_id, self.entity_relation, self.label, self.property_key, self.property_value])


# --------------- 字符串中 ----------------------
# ----------------------------------------------

# 句子中的一段短语
class NounPhrase(object):
    # words是整个句子分词后的word list
    def __init__(self, words, phrase_list):
        # phrase_list is a str_list
        if words is None:
            self.phrase_index_list = None  # phrase所包含词在words中的index
            self.phrase_str_list   = phrase_list  # phrase所包含词的list
            self.phrase_str        = "".join(self.phrase_str_list)  # phrase的字符串表示
            self.phrase_str_list_for_search = list(jieba.cut_for_search(self.phrase_str)) # phrase使用结巴的cut_for_search得到的词表
        # phrase_list is a index_list
        else:
            self.phrase_index_list = phrase_list
            # filter and re-cut
            self.phrase_str_list   = list(jieba.cut(str_filter("".join([words[index] for index in phrase_list]))))
            self.phrase_str        = "".join(self.phrase_str_list)
            self.phrase_str_list_for_search = list(jieba.cut_for_search(self.phrase_str))

# 一个phrase和entity匹配的结构
# 或者是phrase和属性（property）匹配的结构
class EntityCandidate(object):
    def __init__(self, phrase, entity_id, label, property_key, property_value, score):
        self.phrase          = phrase          # 一个句子中的phrase
  
        self.entity_id       = entity_id       # 对应的entity在数据库中的id
        self.label           = label           # 实体标签 课程， 院系 或者 PERSON， 若是properoty 用 label='property'的对象代替
        self.property_key    = property_key    # 检索使用的property
        self.property_value  = property_value  # 
        self.score           = score           # 匹配得分

# ------------- 匹配 ------------------

# 匹配器
class GraphMatcher(object):
    def __init__(self):
        self.entity_lists = {}
        # label
        self.entity_lists["院系"]  = {}
        self.entity_lists["教师"] = {}
        self.entity_lists["课程"]  = {}
        # property
        # 以下表的结构都是（结点id, 属性value）
        self.entity_lists["院系"]["院系中文名"] = load_school_name()
        self.entity_lists["院系"]["中文简称"] = load_school_short()
        self.entity_lists["教师"]["姓名"] = load_teacher_name()
        self.entity_lists["课程"]["课程中文名"] = load_course_name()
        self.entity_lists["课程"]["中文简称"] = load_course_short()

        # 词倒排
        self.inverted_index_word = {}
        # 字倒排
        self.inverted_index_character = {} 

        self.entities = []

        # 建立倒排索引
        for label, entity_lists_by_label in self.entity_lists.items():
            for property_key, property_value_list in entity_lists_by_label.items():
                for entity_id, property_value in property_value_list:
                    # 构造实体对象
                    entity = Entity(entity_id, None, label, property_key, property_value)
                    self.entities.append(entity)
                    # 构建倒排
                    if property_key.endswith('简称'):
                        property_value = property_value[0]
                        property_value = re.sub(r'[^\u4e00-\u9fa5]', '', property_value)
                        if property_value not in self.inverted_index_word:
                            self.inverted_index_word[property_value] = [entity]
                        else:
                            self.inverted_index_word[property_value].append(entity)
                        # character level
                        for character in property_value:
                            if character not in self.inverted_index_character:
                                self.inverted_index_character[character] = [entity]
                            else:
                                self.inverted_index_character[character].append(entity)

                    else:
                        words = property_value
                        for word in words:
                            # filter
                            if word in stop_words: continue
                            if word not in self.inverted_index_word:
                                self.inverted_index_word[word] = [entity]
                            else:
                                self.inverted_index_word[word].append(entity)
                            # character level
                            for character in word:
                                if character not in self.inverted_index_character:
                                    self.inverted_index_character[character] = [entity]
                                else:
                                    self.inverted_index_character[character].append(entity)

        # neo4j
        print("loading neo4j....")
        authenticate("localhost:7474", "neo4j", "esddse000178")
        self.graph = Graph()

    # 从倒排索引建立初始匹配表，一并执行预筛选
    def build_init_to_match_list(self, query, top=20):
        words = list(jieba.cut_for_search(query))

        # init entity cnt
        for entity in self.entities:
            entity.cnt = 0.

        entity_lst = []
        for word in words:
            # 此处过滤包括了去停用词,因为self.inverted_index_word已经没有停用词
            if word not in self.inverted_index_word:
                continue
            for entity in self.inverted_index_word[word]:
                entity.cnt += 1.0
                if entity not in entity_lst:
                    entity_lst.append(entity)

        # 如果根据词索引的entity不足十个，加入字索引
        if len(entity_lst) < 10:
            for word in words:
                if word in stop_words: continue
                for character in word:
                    if character not in self.inverted_index_character:
                        continue
                    for entity in self.inverted_index_character[character]:
                        entity.cnt += 1.0
                        if entity not in entity_lst:
                            entity_lst.append(entity)

        # sort by cnt
        # 预筛选
        entity_lst.sort(key=lambda entity: entity.cnt / min(len(query), len("".join(entity.property_value))), reverse=True)

        return entity_lst[:top] 


    # ------------------ 分数计算 ------------------------------
    # ----------------------------------------------------------

    # 覆盖率，使用最长公共子序列计算
    def coverage_rate(self, lst1, lst2):
        len1 = len(lst1) + 1
        len2 = len(lst2) + 1

        matrix = [[0 for j in range(len2)] for i in range(len1)]

        for i in range(1, len1):
            for j in range(1, len2):
                index1 = i-1
                index2 = j-1

                if lst1[index1] == lst2[index2]:
                    matrix[i][j] = max(matrix[i-1][j-1]+1, matrix[i-1][j], matrix[i][j-1])
                else:
                    matrix[i][j] = max(matrix[i-1][j-1], matrix[i-1][j], matrix[i][j-1])

        return float(matrix[-1][-1]) / len(lst1)

    # 编辑距离
    def edit_distance(self, lst1, lst2):
        len1 = len(lst1) + 1
        len2 = len(lst2) + 1

        matrix = [[float(max(i,j)) if i == 0 and j != 0 or i != 0 and j == 0 else 0 for j in range(len2)] for i in range(len1)]

        for i in range(1, len1):
            for j in range(1, len2):
                index1 = i-1
                index2 = j-1

                if lst1[index1] == lst2[index2]:
                    matrix[i][j] = matrix[i-1][j-1] 
                else:
                    matrix[i][j] = min(matrix[i-1][j], matrix[i-1][j-1], matrix[i][j-1]) + 1

        return float(matrix[-1][-1])

    # 字级别的匹配
    def overlap_character_score(self, phrase1, phrase2):
        max_len = max(len(phrase1.phrase_str), len(phrase2.phrase_str))

        coverage = self.coverage_rate(phrase1.phrase_str, phrase2.phrase_str)
        distance = self.edit_distance(phrase1.phrase_str, phrase2.phrase_str)
        score =  0.5 * (1. - distance / max_len) + 0.5 * coverage

        return score


    # 词级别的匹配
    def overlap_word_score(self, phrase1, phrase2):
        max_len = max(len(phrase1.phrase_str_list), len(phrase2.phrase_str_list))

        coverage = self.coverage_rate(phrase1.phrase_str_list, phrase2.phrase_str_list)
        distance = self.edit_distance(phrase1.phrase_str_list, phrase2.phrase_str_list)
        score =  0.5 * (1. - distance / max_len) + 0.5 * coverage

        return score


    # phrease if a word list
    # param: phrase 是一个word list
    # return: float
    def overall_score(self, ptype, phrase1, phrase2):
        
        score_character = self.overlap_character_score(phrase1, phrase2)
        score_word = self.overlap_word_score(phrase1, phrase2)

        print(phrase1.phrase_str_list, phrase2.phrase_str_list)
        print("score_character:", score_character, " score_word:", score_word)

        # 如果遇到"XXX简称"或者姓名，只匹配字，因为无法分词
        if ptype.endswith("简称") or ptype == "姓名":
            return score_character
        if score_character == 1:
            return score_character

        return 0.5 * score_word + 0.5 * score_character


    # ----------------- 匹配 ----------------------------
    # --------------------------------------------------

    # 在字符串中匹配实体
    # param: phrase 是字符串
    # to_match_list: 一个entity list
    # return: EntityCandidate list
    def match_entity(self, phrase, to_match_list, threshold=0.1, top=10):
        candidates = []

        for entity in to_match_list:
            # 筛选出entity而不是property
            if entity.label != 'property':
                entity_id      = entity.entity_id
                relation       = entity.entity_relation
                label          = entity.label
                property_key   = entity.property_key
                property_value = entity.property_value

                # entity 匹配 relation和value

                # value
                score = self.overall_score(property_key, phrase, NounPhrase(None, property_value))
                if score > threshold:
                    candidates.append(EntityCandidate(phrase, entity_id, label, property_key, "".join(property_value), score))

                if relation is not None:
                    # relation
                    score = self.overall_score("relation", phrase, NounPhrase(None, [relation]))
                    if score > threshold:
                        candidates.append(EntityCandidate(phrase, entity_id, label, property_key, "".join(property_value), score))

        candidates.sort(key=lambda item: item.score, reverse=True)

        return candidates[:top]


    # 在字符串中匹配property,和match_entity基本一致
    def match_property(self, phrase, to_match_list, threshold=0.10, top=10):
        candidates = []

        for property_ in to_match_list:
            if property_.label == 'property':
                entity_id      = property_.entity_id
                property_key   = property_.property_key
                property_value = property_.property_value

                # property 匹配 key
                score = self.overall_score("property", phrase, NounPhrase(None, [property_key]))
                if score > threshold:
                    candidates.append(EntityCandidate(phrase, entity_id, "property", property_key, property_value, score))

        candidates.sort(key=lambda item: item.score, reverse=True)

        return candidates[:top]

    

    # 在neo4j图上选择一个点，返回结点属性和相关结点
    def generate_to_match_list(self, candidate_entity, filter_str):
        to_match_list = []

        # 通过id匹配该结点
        query = "MATCH (entity) WHERE id(entity)=%s RETURN id(entity), entity" % (candidate_entity.entity_id)
        result = self.graph.data(query)[0]

        # 得到此entity的prperty
        entity_id = result['id(entity)']
        for key, value in dict(result['entity']).items():
            if key == 'name': continue
            # filter
            if not is_string_overlap(key, filter_str) and not is_string_overlap(value, filter_str):
                continue
            to_match_list.append(Entity(entity_id, None, "property", key, value))

        # 得到与此entity相关联的entity和relationship
        query = "MATCH (entity1)-[relation]->(entity2) WHERE id(entity1)=%s RETURN type(relation), id(entity2), entity2" % (candidate_entity.entity_id)
        results = self.graph.data(query)

        for result in results:
            entity_id = result['id(entity2)']
            relation  = result['type(relation)']
            property_dict = dict(result['entity2'])

            # filter
            relation_in_string = True
            if not is_string_overlap(relation, filter_str):
                relation_in_string = False

            if '院系名' in property_dict:
                if relation_in_string or is_string_overlap(property_dict['院系名'], filter_str):
                    to_match_list.append(Entity(entity_id, relation, '院系', '院系名', property_dict['院系名']))
            if '院系简称' in property_dict:
                if relation_in_string or is_string_overlap(property_dict['院系简称'], filter_str):
                    to_match_list.append(Entity(entity_id, relation, '院系', '院系简称', property_dict['院系简称']))
            if '姓名' in property_dict:
                if relation_in_string or is_string_overlap(property_dict['姓名'], filter_str):
                    to_match_list.append(Entity(entity_id, relation, '教师', '姓名', property_dict['姓名']))
            if '课程名' in property_dict:
                if relation_in_string or is_string_overlap(property_dict['课程名'], filter_str):
                    to_match_list.append(Entity(entity_id, relation, '课程', '课程名', property_dict['课程名']))
            if '课程简称' in property_dict:
                if relation_in_string or is_string_overlap(property_dict['课程简称'], filter_str):
                    to_match_list.append(Entity(entity_id, relation, '课程', '课程简称', property_dict['课程简称']))

        return to_match_list


if __name__ == "__main__":
    matcher = GraphMatcher()