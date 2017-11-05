# coding:utf-8

'''
定义一个类似beam search的算法
在图上寻找一个最佳匹配
'''

import os
import sys
import threading

lock = threading.Lock()

sys.path.append('.')
sys.path.append('..')

from qaGraph.graphMatcher   import Entity, NounPhrase, EntityCandidate, GraphMatcher
from qaGraph.questionParser import Arc, Chunk, QuestionParser

epsilon = 1e-30

# state in beam search
class MatchState(object):
    def __init__(self, matched, remain, score, to_match_list):
        self.matched = matched               # 已经match的部分
        self.remain  = remain                # 句子中还剩下的部分
        self.score   = score                 # 已经match部分的得分
        self.to_match_list = to_match_list   # 接下来需要match的list

    # 已经match了多少步
    def step(self):
        return len(self.matched)

    # 该state是否match完毕
    def is_finished(self):
        return True if len(self.remain) == 0 else False

    # final_score每个match的平均分
    def final_score(self):
        return self.score / (float(self.step()) + epsilon)  # epsilon防止除0错误

    # 输出调试信息
    def print(self):
        print()
        print("---- state----")
        print("matched: ", self.matched)
        print("remain: ", self.remain)
        print("final_score: ", self.final_score())
        
        print("to_match_list: ")
        if len(self.to_match_list) > 100:
            print("too much! ", len(self.to_match_list))
        else:
            for entity in self.to_match_list:
                entity.print()
        
        print('---------------')
        print()

# 判断beam search是否终止
def to_terminate(state_list):

    # 若state中无state，即当前轮数无扩展则终止
    if len(state_list) == 0:
        return True

    # 剩下的state都扩展完毕则终止
    all_finished = True
    for state in state_list:
        if len(state.remain) > 0:
            all_finished = False
            break

    return all_finished

# 在state_list中选取得分最高的top个进行下一轮扩展
def select_state(state_list, top=10):
    state_list.sort(key=lambda state: state.final_score(), reverse=True)
    return state_list[:top]



# 注: index_list 和 words的范围不一样
def beam_search(parser, matcher, words, postags, out_arcs, root_index, index_list):

    # 初始状态
    init_state = MatchState([], index_list, 0., matcher.build_init_to_match_list("".join(words)))
    state_list = [init_state]

    # 开始迭代扩展
    i = 0
    while not to_terminate(state_list):
        i += 1
        print ('-------------------- ', i, ' -----------------')
        for state in state_list:
            state.print()

        new_state_list = []
        threads = []
        # 遍历每个state
        for state in state_list:

            # 若该state已经扩展完
            if state.is_finished():
                new_state_list.append(state)
                continue

            # 开始匹配
            # ====================

            # 剩余字符串中可能的 phrase
            candidate_phrases = parser.extract_possible_noun_phrase(words, postags, out_arcs, state.remain)


            # 可能的匹配
            candidate_entities = []
            for candidate_phrase in candidate_phrases:
                '''
                print("candidates:")
                print(candidate_phrase.phrase_str_list)
                '''
                if candidate_phrase.phrase_index_list == list(state.remain):
                    candidate_entities += matcher.match_property(candidate_phrase, to_match_list=state.to_match_list)
                else:
                    candidate_entities += matcher.match_entity(candidate_phrase, to_match_list=state.to_match_list)
            candidate_entities.sort(key=lambda item: item.score, reverse=True)

            '''
            print("== match ==")
            for candidate_entity in candidate_entities:
                print(candidate_entity.property_value, " ", candidate_entity.score)
            '''

            # 根据匹配生成新的state
            for candidate_entity in candidate_entities:
                matched       = state.matched + [(candidate_entity.phrase.phrase_str_list, candidate_entity.property_key, candidate_entity.property_value, candidate_entity.score)]
                remain        = parser.subtree(out_arcs, root_index, parser.compute_remain(state.remain, candidate_entity.phrase.phrase_index_list))
                remain_str    = "".join([words[index] for index in remain])
                score         = state.score + candidate_entity.score
                to_match_list = matcher.generate_to_match_list(candidate_entity, remain_str)

                new_state = MatchState(matched, remain, score, to_match_list)
                new_state_list.append(new_state)

        state_list = select_state(new_state_list)


    return state_list




