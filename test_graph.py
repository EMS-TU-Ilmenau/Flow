import sys
from flow import Graph
'''
import logging
logging.basicConfig(filename='example.log', filemode='w', level=logging.DEBUG)
'''
g = Graph(sys.argv[1])
res = g.process()
print(res)