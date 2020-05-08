from pprint import pprint
from pg import SLRParser
from pg.grammar import augmented, Grammar
from pg.items import item_repr, lr0_collection


# Simplified regular expressions SLR(1)-grammar
productions = [
    ['E', 'E', '+', 'T'],
    ['E', 'T'],
    ['T', 'T', '*', 'F'],
    ['T', 'F'],
    ['F', '(', 'E', ')'],
    ['F', 'id'] 
]

print('Augmented grammar:')
grammar = Grammar(productions)
aug_grammar = augmented(grammar)
pprint(list(enumerate(aug_grammar.productions)))


print('Canonical collection of LR(0)-item sets:')
collection = lr0_collection(aug_grammar)

for item_set in collection.item_sets:
    pprint([item_repr(item, aug_grammar) for item in item_set])
pprint(collection.transitions)


# Parsing
parser = SLRParser(grammar)

print('SLR(1)-parser action table:')
pprint(list(enumerate(parser.action)))

print('SLR(1)-parser goto table:')
pprint(list(enumerate(parser.goto)))

string = ['id', '+', 'id']

print(f'Right-most derivation for {" ".join(string)}:')
derivation = parser.run(string)
pprint(derivation)

# TODO: parse tree

