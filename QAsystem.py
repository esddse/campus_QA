# coding:utf-8

import os
import sys
import time
from optparse import OptionParser

import pymysql

from util import *
from qaGraph.questionParser import Arc, Chunk, QuestionParser
from qaGraph.graphMatcher   import NounPhrase, EntityCandidate, GraphMatcher
from qaGraph.algorithm      import MatchState, beam_search




class QuestionAnsweringSystem(object):
    
    def __init__(self):
        self.parser  = QuestionParser()
        self.matcher = GraphMatcher()
        
    # 回答一个问题
    def answer_question(self, question, is_server=False):

        # 基本分词、词性标注、依存句法标注等
        words, postags, out_arcs, in_arcs = self.parser.parse_sentence(question)

        print('\t'.join(map(str, range(len(words)))))
        print('\t'.join(words))
        print('\t'.join(postags))
        print('\t'.join('%d:%s' % (in_arcs[i].start, in_arcs[i].relation) for i in range(len(in_arcs))))

        # 基本句子分块
        chunks = self.parser.split_by_pred(words, out_arcs)
        chunk_strs = [chunk.str for chunk in chunks]
        print("chunk_strs: ", chunk_strs)
        
        # 只有一个chunk情况，
        if len(chunks) == 1:
            state_list = beam_search(self.parser, self.matcher, words, postags, out_arcs, chunks[0].root_index, chunks[0].index_list)
            print('----------------- end ------------------')
            for state in state_list:
                state.print()

        elif len(chunks) == 2:
            chunk0_has_question_word = self.parser.check_question_words(chunks[0])
            chunk1_has_question_word = self.parser.check_question_words(chunks[1])

            if chunk0_has_question_word and chunk1_has_question_word:
                print("【ERR】 too many question words!")
                return "No answer"
            elif chunk0_has_question_word and not chunk1_has_question_word:
                main_chunk     = chunks[1]
                question_chunk = chunks[0]
            elif not chunk0_has_question_word and chunk1_has_question_word:
                main_chunk     = chunks[0]
                question_chunk = chunks[1]
            else:
                print("【ERR】 cannot find question word!")
                return "No answer"

            self.parser.question_word_conversion(words, postags, question_chunk)
            words, postags, out_arcs, in_arcs, combined_chunk = self.parser.chunk_combination(words, postags, out_arcs, in_arcs, main_chunk, question_chunk)

            print('\t'.join(map(str, range(len(words)))))
            print('\t'.join(words))
            print('\t'.join(postags))
            print('\t'.join('%d:%s' % (in_arcs[i].start, in_arcs[i].relation) for i in range(len(in_arcs))))

            state_list = beam_search(self.parser, self.matcher, words, postags, out_arcs, combined_chunk.root_index, combined_chunk.index_list)
            print('----------------- end ------------------')
            for state in state_list:
                state.print()

        else:
            print("【ERR】 chunks > 2 ")
            

        sorted_results = []
        # answer collection
        for state in state_list:
            sorted_results.append((state.matched[-1][2], state.final_score()))
        if len(sorted_results) == 0:
            sorted_results = None    
        # unique
        else:
            sorted_results = list(set(sorted_results))
            # sort by score
            sorted_results.sort(key=lambda item: item[1], reverse=True)

        # 以下部分和问答服务有关，不修改
        # ==========================================================

        if is_server == True:
            answers_text = ''
            if sorted_results is None or len(sorted_results) == 0:
                answers_text = 'No Answer\t0\n\n'
            else:
                if len(sorted_results) > 10:
                    sorted_results = sorted_results[:10]
                answers = []
                for result in sorted_results:
                    if result[0] not in answers:
                        answers.append(result[0])
                        answers_text += (str(result[0]) + '\t' + str(result[1]) + '\n\n')
            return answers_text
        else:
            if sorted_results is None:
                return "No Answer"
            else:
                return sorted_results[0][0]



    # 回答一列表的问题,并输出
    def answer_questions(self, questions, write_to_file=False):
        answers = []
        for question in questions:
            asnwer = self.answer_question(question)
            answers.append(asnwer)
        if write_to_file:
            with open('./data/test_answers', 'w', encoding='utf8') as f:
                for asnwer in answers:
                    f.write(answer+'\n')
            print('all answers are writen to file: ./data/test_answers')
        else:
            for question, answer in zip(questions, answers):
                print(question, '\n答:', answer)


def main():
    # define cmd line parameter
    parser = OptionParser()
    parser.add_option("-s", "--server",
                      action="store_true",
                      dest="is_server",
                      help="be server")
    parser.add_option("-f", "--file",
                      action="store",
                      type="string",
                      dest="filepath",
                      help="path of input file, the file should contain questions only")

    (options, args) = parser.parse_args()

    # qa system
    question_answering_system = QuestionAnsweringSystem()

    # if system work for webapp, read question from database
    if options.is_server == True:
        db = pymysql.connect('localhost', 'root', 'webkdd', 'esddse', charset='utf8')
        cursor = db.cursor()

        while True:
            try:
                cursor.execute("SELECT * FROM campusQA WHERE is_processed=0 LIMIT 1000")
                results = cursor.fetchall()
                for row in results:
                    question = row[0]
                    answers  = question_answering_system.answer_question(question, is_server=True)
                    print(answers)
                    print(question)
                    answers.replace('"', r'\"')
                    answers.replace("'", r"\'")
                    question.replace('"', r'\"')
                    question.replace("'", r"\'")
                    print("UPDATE campusQA SET answer='%s', is_precessed=1, WHERE question LIKE '%s'" % (answers, question))
                    cursor.execute("UPDATE campusQA SET answer='%s', is_processed=1 WHERE question LIKE '%s'" % (answers, question))
                db.commit()
            except Exception as e:
                db.rollback()
                print(e)
            time.sleep(0.1)

        cursor.close()
        db.close()

    else:
        # read questions from file or from cmd line
        if options.filepath is None:
            while True:
                print ('please type in you question (in Chinese), "exit" or "quit" to exit this program:')
                question = input()
                if question == 'exit' or question == 'quit':
                    break
                elif question == '':
                    continue
                question_answering_system.answer_questions([question])
        else:
            with open(options.filepath, 'r', encoding='utf8') as f:		
                questions = [line.strip() for line in f]
                question_answering_system.answer_questions(questions, write_to_file=True)


if __name__ == '__main__':
	main()