from pprint import pprint
from pg.grammar import Grammar
from pg.items import lr0_collection


# Simplified regular expressions SLR(1)-grammar
productions = [
    ['E', 'E', '+', 'T'],
    ['E', 'T'],
    ['T', 'T', '*', 'F'],
    ['T', 'F'],
    ['F', '(', 'E', ')'],
    ['F', 'id'] 
]

print('Grammar: ')
pprint(productions)
grammar = Grammar(productions)


print('Canonical collection of LR(0)-items:')
collection = lr0_collection(grammar)
pprint(collection)

