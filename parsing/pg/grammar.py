from pg.util import EPS


def symbols(productions):
    # NOTE: implicit assumption: no redundant symbols
    terminals, non_terminals = set(), set()

    for prod in productions:
        non_terminals.add(prod[0])

    for prod in productions:
        for symbol in prod[1:]:
            if symbol != EPS and symbol not in non_terminals:
                terminals.add(symbol)

    return terminals, non_terminals


class Grammar:
    def __init__(self, productions):
        self.productions = productions

        t, nt = symbols(productions)
        self.terminals = t
        self.non_terminals = nt
        
        # TODO: topological sorting?
        self.start = productions[0][0]


def augmented(grammar):
    n_grammar = Grammar(grammar.productions)
    n_start = n_grammar.start + '<AUG>'
    aux_prod = [n_start, n_grammar.start]

    n_grammar.productions = [aux_prod] + n_grammar.productions
    n_grammar.start = n_start
    n_grammar.non_terminals.add(n_grammar.start)
    
    return n_grammar

