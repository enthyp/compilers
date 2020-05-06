from pprint import pprint
from pg import LLParser 
from pg.util import first, follow, Grammar


# Simple arithmetic expressions grammar
productions = [
    ['E', 'T', 'E\''],
    ['E\'', '+', 'T', 'E\''],
    ['E\'', ''],
    ['T', 'F', 'T\''],
    ['T\'', '*', 'F', 'T\''],
    ['T\'', ''],
    ['F', '(', 'E', ')'],
    ['F', 'id'] 
]
grammar = Grammar(productions)

# FIRST(1) and FOLLOW(1)
first_sets = first(grammar)
follow_sets = follow(grammar, first_sets)

pprint(first_sets)
pprint(follow_sets)

parser = LLParser(grammar)
pprint(parser.table)

