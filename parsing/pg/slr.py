from collections import defaultdict
from pg.error import ConflictError, InputError
from pg.grammar import augmented
from pg.items import lr0_collection
from pg.util import END, EPS, first, follow

ACCEPT = 'ACCEPT'
SHIFT = 'SHIFT'
REDUCE = 'REDUCE'


# Insert state -> GOTO table, action -> action table
def insert(table, state, symbol, action_state):
    if symbol in table[state]:
        cur_action_state = table[state][symbol]
        raise ConflictError(f'Conflict for ({state}, {symbol}): {cur_action_state} and {action_state}')
    else:
        table[state][symbol] = action_state

 
def build_table(grammar):
    first_sets = first(grammar)
    follow_sets = follow(grammar, first_sets)

    aug_grammar = augmented(grammar)
    collection = lr0_collection(aug_grammar)

    action = [{} for _ in range(len(collection))]
    goto = [{} for _ in range(len(collection))]

    for state, item_set in enumerate(collection.item_sets):
        # Action table
        for item in item_set:
            prod = aug_grammar.productions[item.prod_no]

            if item.position < len(prod) - 1 and prod[item.position + 1] in grammar.terminals:
                # Shift
                t = prod[item.position + 1]
                next_state = collection.transitions[(state, t)]
                insert(action, state, t, (SHIFT, next_state))
            
            elif item.position == len(prod) - 1:
                # Reduce
                NT = prod[0]

                if NT == aug_grammar.start:
                    insert(action, state, END, ACCEPT)
                else:          
                    for symbol in follow_sets[NT]:
                        insert(action, state, symbol, (REDUCE, item.prod_no))

        # Goto table
        for NT in grammar.non_terminals:
            next_state = collection.transitions.get((state, NT), None)
            if next_state: 
                insert(goto, state, NT, next_state)

    return action, goto


# Parsers could have common base class, LR parsers yet another etc...
class SLRParser:
    def __init__(self, grammar):
        self.grammar = grammar
        self.table = build_table(grammar)

    def run(self, string):
        pass

