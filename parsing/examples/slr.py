from pprint import pprint
from pg.grammar import augmented, Grammar
from pg.items import item_repr, lr0_collection
from pg.slr import build_table


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


action, goto = build_table(grammar)

print('SLR(1)-parser action table:')
pprint(action)

print('SLR(1)-parser goto table:')
pprint(goto)

