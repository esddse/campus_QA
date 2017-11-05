
# coding:utf8

from questionParser import Arc, Chunk, QuestionParser
from graphMatcher import NounPhrase, EntityCandidate, GraphMatcher
from algorithm import beam_search

def main():
    parser  = QuestionParser()
    matcher = GraphMatcher()

    while True:
        print("请输入句子:")
        question = input()
        if question == "": continue

        # 基本分词、词性标注、依存句法标注等
        words, postags, out_arcs, in_arcs = parser.parse_sentence(question)

        # 输出（调试信息）
        print('\t'.join(map(str, range(len(words)))))
        print('\t'.join(words))
        print('\t'.join(postags))
        print('\t'.join('%d:%s' % (in_arcs[i].start, in_arcs[i].relation) for i in range(len(in_arcs))))

        # 基本句子分块，从谓语动词分开
        chunks = parser.split_by_pred(words, out_arcs)
        chunk_strs = [chunk.str for chunk in chunks]
        print("chunk_strs: ", chunk_strs)
        
        # 只有一个chunk情况，如“高等数学的老师”
        # 没有谓语动词，不是完整句子结构
        # 一般就是检索目标
        if len(chunks) == 1:
            state_list = beam_search(parser, matcher, words, postags, out_arcs, chunks[0].root_index, chunks[0].index_list)
            print('----------------- end ------------------')
            for state in state_list:
                state.print()

        # 有两个chunk的情况，从谓语动词分开
        elif len(chunks) == 2:

            # 将两个块分成有疑问词的块和没有疑问词的块
            # “谁是高等数学的老师”，“高等数学的老师是谁”
            # 都可以分成：
            # 没疑问词的块（主块）:“高等数学的老师”
            # 有疑问词的块：“谁”
            chunk0_has_question_word = parser.check_question_words(chunks[0])
            chunk1_has_question_word = parser.check_question_words(chunks[1])

            if chunk0_has_question_word and chunk1_has_question_word:
                print("【ERR】 too many question words!")
                continue
            elif chunk0_has_question_word and not chunk1_has_question_word:
                main_chunk     = chunks[1]
                question_chunk = chunks[0]
            elif not chunk0_has_question_word and chunk1_has_question_word:
                main_chunk     = chunks[0]
                question_chunk = chunks[1]
            else:
                print("【ERR】 cannot find question word!")
                continue

            # 对疑问词的处理 【注：这部分没有理论基础，纯是我的臆想】
            # 有时候疑问词并不带有信息，并且不能在数据库中检索
            # 比如“谁是高等数学的老师”，和“高等数学的老师”在这个系统中应该是等价的
            # 此时疑问词“谁”并不带有任何信息，直接去掉就可以
            # “高等数学什么时候上课”的“什么”也没提供信息
            # 然是“高等数学在哪上课”和“高等数学在上课”、“高等数学上课”的意义就完全不同
            # 因为“哪”包含了“地点”的意思
            parser.question_word_conversion(words, postags, question_chunk)
            # 将被谓语动词分开的两个块拼合起来，使句子句有完整信息
            words, postags, out_arcs, in_arcs, combined_chunk = parser.chunk_combination(words, postags, out_arcs, in_arcs, main_chunk, question_chunk)

            print('\t'.join(map(str, range(len(words)))))
            print('\t'.join(words))
            print('\t'.join(postags))
            print('\t'.join('%d:%s' % (in_arcs[i].start, in_arcs[i].relation) for i in range(len(in_arcs))))

            # 在图上进行检索
            state_list = beam_search(parser, matcher, words, postags, out_arcs, combined_chunk.root_index, combined_chunk.index_list)
            print('----------------- end ------------------')
            for state in state_list:
                state.print()

        else:
            print("【ERR】 chunks > 2 ")
            continue


if __name__ == "__main__":
    main()
