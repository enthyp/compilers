from collections import defaultdict 
from graphviz import Digraph
from uuid import uuid4

EPS = ''
END = '$'


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


def first(grammar):
    first_sets = defaultdict(set)
    
    # Deal with terminals
    for t in grammar.terminals:
        first_sets[t].add(t)

    # Iteratively extend FIRST(1) sets as long as possible
    while True:
        changed = False
        for prod in grammar.productions:
            nt = prod[0]
            init_size = len(first_sets[nt])

            # Check empty productions
            if len(prod) == 2 and prod[1] == EPS:
                first_sets[nt].add(EPS)
                continue

            for symbol in prod[1:]:
                if symbol == EPS:
                    continue
                first_sets[nt].update(first_sets[symbol] - {EPS})
                if EPS not in first_sets[symbol]:
                    break
            else:
                first_sets[nt].add(EPS)
        
            changed = changed or init_size != len(first_sets[nt])
        if not changed:
            break

    return dict(first_sets)


# NOTE: FOLLOW(1) for non-terminals only (for terminals - not necessary)
def follow(grammar, first_sets):
    follow_sets = defaultdict(set)
    
    # Initialize
    follow_sets[grammar.start].add(END)

    # Iteratively expand FOLLOW(1) sets as long as possible
    while True:
        changed = False
        for prod in grammar.productions:
            nt = prod[0]

            for i, symbol in enumerate(prod[1:]):
                if symbol == EPS or symbol in grammar.terminals:
                    continue

                for succ in prod[i + 2:]:
                    changed = changed or (first_sets[succ] - {EPS} - follow_sets[symbol])
                    follow_sets[symbol].update(first_sets[succ] - {EPS})
                   
                    if EPS not in first_sets[succ]:
                        break
                else:
                    changed = changed or (follow_sets[nt] - follow_sets[symbol])
                    follow_sets[symbol].update(follow_sets[nt])

        if not changed:
            break

    return dict(follow_sets)


def parse_tree(derivation, grammar):
    graph = Digraph('parse_tree', node_attr={'style': 'filled'})
    root_id = str(uuid4())
    graph.node(root_id, label=grammar.start)

    def visualize_prod(node_id, num):
        prod_num = derivation[num]
        prod = grammar.productions[prod_num]

        for symbol in prod[1:]:
            new_id = str(uuid4())
            graph.node(new_id, label=symbol)
            graph.edge(node_id, new_id)
            
            if symbol in grammar.non_terminals:
                num = visualize_prod(new_id, num + 1)
                                
        return num

    visualize_prod(root_id, 0)
    graph.render('out/parse_tree', view=True)

