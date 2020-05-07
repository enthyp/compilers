from collections import defaultdict
from pg.util import EPS


def augment(grammar):
    n_start = grammar.start + '\''
    grammar.orig_start = grammar.start
    grammar.start = n_start

    aux_prod = [n_start, grammar.orig_start]
    grammar.productions = [aux_prod] + grammar.productions
    grammar.non_terminals.add(n_start)


def reset(grammar):
    n_start = grammar.start
    grammar.start = grammar.orig_start
    del grammar.orig_start

    grammar.productions = grammar.productions[1:]
    grammar.non_terminals.remove(n_start)


def lr0_collection(grammar):
    collection = defaultdict(set)

    # Augment the grammar and initialize collection of LR(0)-item sets
    augment(grammar)

    init_item = ((grammar.start, grammar.orig_start), 0)
    collection[EPS].add(init_item)
    collection[EPS] = lr0_closure(collection[EPS], grammar)

    # Build item sets for all viable prefixes
    while True:
        changed = False
        viable_prefixes = set(collection.keys())

        for prefix in viable_prefixes:
            item_set = collection[prefix]
            for symbol in grammar.non_terminals | grammar.terminals:
                goto_set = lr0_goto(item_set, symbol, grammar)

                if not goto_set or goto_set in collection.values():
                    continue

                collection[prefix + symbol] = goto_set
                changed = True

        if not changed:
            break

    reset(grammar)
    return dict(collection)


def lr0_closure(item_set, grammar):
    closure = item_set.copy()
    
    while True:
        new_items = set()

        # TODO: no need to consider all items every time
        for item in closure:
            prod, pos = item
            if pos < len(prod) - 1 and prod[pos + 1] in grammar.non_terminals:
                NT = prod[pos + 1]

                # Find all productions with this NT on the left
                rhss = [tuple(prod) for prod in grammar.productions if prod[0] == NT]
                
                for rhs in rhss:
                    new_items.add((rhs, 0))

        if new_items <= closure:
            break
        else:
            closure.update(new_items)

    return closure


def lr0_goto(item_set, symbol, grammar):
    goto_set = set()
    
    for item in item_set:
        prod, pos = item
        if pos < len(prod) - 1 and prod[pos + 1] == symbol:
            goto_set.add((prod, pos + 1))

    return lr0_closure(goto_set, grammar)


def lr1_items(grammar):
    return {}


def lr1_closure(item):
    pass


def lr1_goto(item):
    pass

