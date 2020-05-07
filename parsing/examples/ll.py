from pprint import pprint
from pg import LLParser 
from pg.grammar import Grammar
from pg.util import first, follow, parse_tree


# Simplified regular expressions LL(1)-grammar
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

print('Grammar: ')
pprint(productions)
grammar = Grammar(productions)

# FIRST(1) and FOLLOW(1) sets
first_sets = first(grammar)
follow_sets = follow(grammar, first_sets)

print('FIRST: ')
pprint(first_sets)

print('FOLLOW: ')
pprint(follow_sets)


# Parsing
parser = LLParser(grammar)

print('LL(1) parser table: ')
pprint(parser.table)

string = ['(', 'id', '+', 'id', ')', '*', 'id']

print(f'Left-most derivation for {" ".join(string)}:')
derivation = parser.run(string)
pprint(derivation)

# Parse tree
parse_tree(derivation, grammar)

