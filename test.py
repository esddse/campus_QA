
# encoding: utf-8

from util import *
from pyltp import Segmentor
from pyltp import Postagger
from pyltp import Parser

def edit_distance(lst1, lst2):
    len1 = len(lst1) + 1
    len2 = len(lst2) + 1

    matrix = [[max(i,j) if i == 0 and j != 0 or i != 0 and j == 0 else 0 for j in range(len2)] for i in range(len1)]
    
    for i in range(1, len1):
        for j in range(1, len2):
            
            index1 = i-1
            index2 = j-1

            if lst1[index1] == lst2[index2]:
                matrix[i][j] = matrix[i-1][j-1]
            else:
                matrix[i][j] = min(matrix[i-1][j], matrix[i-1][j-1], matrix[i][j-1]) + 1

    print(matrix)
    return matrix[-1][-1]

def lcs(lst1, lst2):
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

    print(matrix)
    return matrix[-1][-1]


cur_path = os.path.dirname(os.path.abspath(__file__)) + '/'
self.segmentor = Segmentor()
self.segmentor.load(cur_path + 'ltp_data/cws.model')
self.postagger = Postagger()
self.postagger.load(cur_path + 'ltp_data/pos.model')
self.parser = Parser()
self.parser.load(cur_path + 'ltp_data/parser.model')

print(edit_distance('123', '1020300'))
print(lcs('123', '1020300'))