from collections import defaultdict
from pg.util import EPS, first, follow


class ConflictError(Exception):
    """Conflict in parsing table - non LL(1) grammar."""


def insert(table, non_terminal, terminal, num_prod):
    if terminal in table[non_terminal]:
        cur_num_prod = table[non_terminal][terminal]
        raise ConflictError(f'Conflict for ({non_terminal}, {terminal}): {cur_num_prod} and {num_prod}')
    else:
        table[non_terminal][terminal] = num_prod
    

def build_table(grammar):
    first_sets = first(grammar)
    follow_sets = follow(grammar, first_sets)

    parse_table = defaultdict(dict)
    for i, prod in enumerate(grammar.productions):
        nt = prod[0]

        if len(prod) == 2 and prod[1] == EPS:
            # Empty production
            for t in follow_sets[nt]:
                insert(parse_table, nt, t, i)
        else:
            for j, symbol in enumerate(prod[1:]):
                for t in first_sets[symbol]:
                    insert(parse_table, nt, t, i)
                
                if EPS not in first_sets[symbol]:
                    break
            else:
                for t in follow_sets[nt]:
                    insert(parse_table, nt, t, i)

    return dict(parse_table)


class LLParser:
    def __init__(self, grammar):
        self.table = build_table(grammar)

