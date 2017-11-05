# coding: utf-8


'''
这个模块和句法分析有关
'''

import os
import sys

sys.path.append('.')
sys.path.append('..')

import jieba


from pyltp import Segmentor
from pyltp import Postagger
from pyltp import Parser

from util import load_question_words
from qaGraph.graphMatcher import NounPhrase, EntityCandidate

# arc for dependency parsing
class Arc(object):
    def __init__(self, start, end, relation):
        self.start    = start
        self.end      = end
        self.relation = relation

# 句子中的一个块
class Chunk(object):
    def __init__(self, words, relation_with_head, root_index, index_list):
        self.relation_with_head = relation_with_head  # 该块的根结点在句子中的成分，如SBV
        self.root_index = root_index                  # 根节点在words中的index
        self.index_list = index_list                  # 整个chunk在words中的index list
        self.str_list   = [words[index] for index in index_list]  # chunk的string list
        self.str        = "".join(self.str_list)      # chunk的string

# 句法分析器
class QuestionParser(object):

    def __init__(self):

        # load tools
        cur_path = os.path.dirname(os.path.abspath(__file__)) + '/'

        # 用户词典，包括所有名称和简称
        jieba.load_userdict(cur_path + "../data/specific/names")

        self.segmentor = Segmentor()
        self.segmentor.load(cur_path + '../ltp_data/cws.model')
        self.postagger = Postagger()
        self.postagger.load(cur_path + '../ltp_data/pos.model')
        self.parser = Parser()
        self.parser.load(cur_path + '../ltp_data/parser.model')

        # question word list
        self.question_words = load_question_words()


    # 句子的基本parse
    def parse_sentence(self, sentence):
        # words    = self.segmentor.segment(sentence)
        words    = list(jieba.cut(sentence))
        postags  = self.postagger.postag(words)
        ltp_arcs = self.parser.parse(words, postags)
        
        # construct in-arc / out-arc map
        out_arcs = {}
        in_arcs  = {}
        for i in range(len(ltp_arcs)):
            end      = i
            start    = ltp_arcs[i].head - 1   # root:-1
            relation = ltp_arcs[i].relation
            arc      = Arc(start, end, relation)

            in_arcs[end] = arc
            if start in out_arcs:
                out_arcs[start].append(arc)
            else:
                out_arcs[start] = [arc]

        return words, postags, out_arcs, in_arcs 

    # 在依存分析树中找到以一个root_index为根的子树,范围是index_range
    def subtree(self, out_arcs, root_index, index_range):

        if len(index_range) == 0:
            return []

        index_list = [root_index]
        
        # bfs
        nodes = [root_index]  # the first layer
        depth = 0
        while len(nodes) > 0:
            new_nodes = []    # the next layer
            for node in nodes:
                if node not in out_arcs or node not in index_range: continue
                for arc in out_arcs[node]:
                    # 去掉不在index_range中的
                    if arc.end not in index_range: continue
                    # 去掉RAD，右依赖，如“的”、“们”
                    if arc.relation == 'RAD' and depth == 0:continue
                    new_nodes.append(arc.end)
            index_list += new_nodes
            nodes = new_nodes
            depth += 1

        index_list.sort()
        return index_list

    # 找到子树，忽略中心结点（即非叶子结点）
    def subtree_no_center(self, out_arcs, root_index, index_range):
        index_list = [root_index]
        for arc in out_arcs[root_index]:
            if arc.end not in index_range: continue
            # 非叶子结点
            if arc.end not in out_arcs[arc.end]:
                index_list.append(arc.end)
        index_list.sort()
        return index_list

    # 计算除去一个短语后，剩下部分有意义的index
    def compute_remain(self, index_full, index_to_delete):
        return [index for index in index_full if index not in index_to_delete]

    # 以谓语动词为中心将句子结构分开
    # return: [chunk1, chunk2, ...]
    def split_by_pred(self, words, out_arcs):
        
        # head index
        head_index = out_arcs[-1][0].end

        chunks = []
        is_split = False
        # the 2nd layer, find SBV
        if head_index in out_arcs:
            for arc in out_arcs[head_index]:
                # 主语
                if arc.relation == "SBV":
                    sbv_index = arc.end
                    sbv_index_list  = self.subtree(out_arcs, sbv_index, range(len(words)))
                    chunks.append(Chunk(words, "SBV", sbv_index, sbv_index_list))
                    is_split = True
                    
                # 宾语，主谓宾结构
                elif arc.relation == "VOB":
                    vob_index = arc.end
                    vob_index_list  = self.subtree(out_arcs, vob_index, range(len(words)))
                    chunks.append(Chunk(words, "VOB", vob_index, vob_index_list))
                    is_split = True

                elif arc.relation == "POB":
                    pob_index = arc.end
                    pob_index_list = self.subtree(out_arcs, pob_index, range(len(words)))
                    chunks.append(Chunk(words, "POB", pob_index, pob_index_list))
                    is_split = True

                # 谓语动词状语，主谓结构
                elif arc.relation == "ADV":
                    adv_index = arc.end
                    adv_index_list  = self.subtree(out_arcs, adv_index, list(range(len(words))))
                    # 由于状语必须要和中心词在一起才有意义
                    adv_index_list.append(head_index)
                    chunks.append(Chunk(words, "ADV", adv_index, adv_index_list))
                    is_split = True

        if not is_split:
            chunks.append(Chunk(words, "HEAD", head_index, range(len(words))))

        return chunks

    # check whether a chunk has question word
    def check_question_words(self, chunk):
        has_question_word = False
        for word in chunk.str_list:
            if word in self.question_words:
                has_question_word = True
                break
        return has_question_word

    # 疑问词转换成查询属性(property)
    def question_word_conversion(self, words, postags, chunk):
        for index in chunk.index_list:
            if words[index] in self.question_words:
                words[index]  = self.question_words[words[index]]
                postags[index] = 'x'

        print("words:", words)

    # chunk融合
    def chunk_combination(self, words, postags, out_arcs, in_arcs, chunk1, chunk2):
        new_str1 = "".join([words[index] for index in chunk1.index_list])
        new_str2 = "".join([words[index] for index in chunk2.index_list])

        # 主语放在前面
        if chunk1.relation_with_head == 'SBV':
            new_str = new_str1 + new_str2
        else:
            new_str = new_str2 + new_str1

        print(new_str)

        words, postags, out_arcs, in_arcs = self.parse_sentence(new_str)

        return words, postags, out_arcs, in_arcs, self.split_by_pred(words, out_arcs)[0]


    # 提取可能的名词短语,为entity的匹配创造条件
    # 如：    地史中的生命的老师
    # 提取出: 地史   地史中  地史中的生命    地史中的生命的老师
    # return [(np1_indices, np1_str), (np2_indices, np2_str), ...]
    def extract_possible_noun_phrase(self, words, postags, out_arcs, chunk_index_list):
        noun_phrases = []
        for index in chunk_index_list:
            if postags[index].startswith('n') or postags[index].startswith('i') or postags[index].startswith('j'):
                noun_phrase_index_list = self.subtree(out_arcs, index, chunk_index_list)
                noun_phrases.append(NounPhrase(words, noun_phrase_index_list))
        return noun_phrases
         


if __name__ == "__main__":
    parser = QuestionParser()
    while True:
        print("请输入句子:")
        question = input()
        words, postags, out_arcs, in_arcs = parser.parse_sentence(question)
        
        print('\t'.join(map(str, range(len(words)))))
        print('\t'.join(words))
        print('\t'.join(postags))
        print('\t'.join('%d:%s' % (in_arcs[i].start, in_arcs[i].relation) for i in range(len(in_arcs))))

        chunks = parser.split_by_pred(words, out_arcs)
        output = ""
        for chunk in chunks:
            output += "".join([words[i] for i in chunk[2]]) + '\t'
        print(output)

        for chunk in chunks:
            nps = parser.extract_possible_noun_phrase(words, postags, out_arcs, chunk[2])
            print("\t".join(nps))




