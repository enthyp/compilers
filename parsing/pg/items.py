from collections import defaultdict
from copy import copy
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple
from pg.util import EPS


@dataclass(frozen=True)
class LR0Item:
    prod_no: int
    position: int


def item_repr(item, grammar):
    prod = grammar.productions[item.prod_no]
    string = f'{prod[0]} -> '
    prepos = prod[:item.position + 1][1:]
    postpos = prod[item.position + 1:]
    string += ' '.join(prepos + ['<POS>'] + postpos)
    return string


@dataclass
class LR0Collection:
    item_sets: List[Set[LR0Item]]
    transitions: Dict[(int, int)] 

    def __len__(self):
        return len(self.item_sets)


def lr0_collection(grammar):
    # Initialize collection of LR(0)-item sets
    init_item = LR0Item(0, 0)
    init_set = lr0_closure({init_item}, grammar)

    item_sets = [init_set]
    transitions = {}

    # Build item sets for all viable prefixes
    while True:
        changed = False
        n_sets = len(item_sets)

        for state in range(n_sets):
            item_set = item_sets[state]

            for symbol in grammar.non_terminals | grammar.terminals:
                goto_set = lr0_goto(item_set, symbol, grammar)

                if not goto_set: 
                    continue

                for j, i_set in enumerate(item_sets):
                    if goto_set == i_set:
                        transitions[(state, symbol)] = j
                        break
                else:
                    transitions[(state, symbol)] = len(item_sets)
                    item_sets.append(goto_set)
                    changed = True

        if not changed:
            break

    return LR0Collection(item_sets, transitions)


def lr0_closure(item_set, grammar):
    closure = copy(item_set)
  
    while True:
        new_items = set()

        # TODO: no need to consider all items every time
        for item in closure:
            prod = grammar.productions[item.prod_no]

            if item.position < len(prod) - 1 and prod[item.position + 1] in grammar.non_terminals:
                NT = prod[item.position + 1]

                # Find all productions with this NT on the left
                rhss = [i for i, prod in enumerate(grammar.productions) if prod[0] == NT]
                new_items.update([LR0Item(rhs, 0) for rhs in rhss])

        if new_items <= closure:
            break
        else:
            closure.update(new_items)

    return closure


def lr0_goto(item_set, symbol, grammar):
    goto_set = set()
    
    for item in item_set:
        prod = grammar.productions[item.prod_no]
        if item.position < len(prod) - 1 and prod[item.position + 1] == symbol:
            goto_set.add(LR0Item(item.prod_no, item.position + 1))

    return lr0_closure(goto_set, grammar)


def lr1_items(grammar):
    return {}


def lr1_closure(item):
    pass


def lr1_goto(item):
    pass

