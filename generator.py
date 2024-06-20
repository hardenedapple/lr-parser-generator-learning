import sys
import enum
from parse_grammar import get_rules
import copy
import itertools as itt
import collections
import logging
logger = logging.getLogger(__name__)

# TODO
#   - Ensure we can handle possibly empty rules
#     (I.e. if a rule could expand to nothing, do we handle that).

class SpecialTok(enum.Enum):
    EOL = 'EOL'
    REDUCE = 'REDUCE'

def all_nonterminals(rules):
    return set(rules.keys())

def transitive_closure(accumulator, cb):
    old = type(accumulator)()
    while old != accumulator:
        old = accumulator
        accumulator = cb(old)
    return accumulator
 
def make_terminal_func(nonterminals):
    def terminal(tok):
        return tok not in nonterminals
    return terminal

def first_from_rules(nonterm, rules):
    ret = set()
    for v in rules.values():
        for r in v:
            ret.update({r[0]} if terminal(r[0]) else [])
    return ret

def make_first_callback(start_token):
    def first_callback(accum):
        ret = copy.deepcopy(accum)
        for nt in accum:
            for s in start_token[nt]:
                ret[nt].update(accum.get(s, set()))
        return ret
    return first_callback

def first(rules):
    prev_mapping = {}
    cur_mapping = {nt: first_from_rules(nt, rules) for nt in nonterminals}
    start_token = {}
    for nt in nonterminals:
        start_token[nt] = [other for other in nonterminals
            if any(r[0] == nt for r in rules[other])]
    return transitive_closure(cur_mapping, make_first_callback(start_token))

def basic_follow_from_rule(rule):
    known_follows = collections.defaultdict(set)
    for idx, tok in enumerate(rule[:-1]):
        if terminal(tok):
            continue
        to_add = rule[idx+1]
        if terminal(to_add):
            known_follows[tok].add(to_add)
        else:
            known_follows[tok].update(FIRST(to_add))
    return known_follows

def make_follow_tc(ends_token):
    def follow_callback(accum):
        ret = copy.deepcopy(accum)
        for nt in accum:
            for e in ends_token[nt]:
                ret[nt].update(accum.get(e, set()))
        return ret
    return follow_callback

def merge_fol(accum, extra):
    for k, v in extra.items():
        accum[k].update(v)

def follow(rules):
    initial = collections.defaultdict(set)
    for rule in itt.chain(*rules.values()):
        merge_fol(initial, basic_follow_from_rule(rule))
    ends_token = {}
    for nt in nonterminals:
        ends_token[nt] = [other for other in nonterminals
             if any(r[-1] == nt for r in rules[other])]
    return transitive_closure(initial, make_follow_tc(ends_token))

class TableEntry:
    def __init__(self, key, rule, point):
        self.point = point
        self.key = key
        self.rule = tuple(rule)
        self.reduce_point = len(rule)
    @classmethod
    def from_rule_and_name(cls, rules, name):
        assert(len(rules[name]) == 1)
        return cls(name, rules[name][0], 0)
    def next_token(self):
        if self.point == self.reduce_point:
            return SpecialTok.REDUCE
        return self.rule[self.point]
    def __repr__(self):
        return '{} = {}{}{}'.format(
            self.key,
            ' '.join(self.rule[:self.point]),
            ' . ',
            ' '.join(self.rule[self.point:]))
    def __hash__(self):
        return hash((self.key, self.rule, self.point))

class TableSet:
    def __init__(self, first_entry):
        self.storage = set([first_entry])
    def shift_hash(self):
        return hash(tuple(set(e.next_token for e in self.storage)))
    @staticmethod
    def add_predictions_1(accum, rules):
        ret = copy.deepcopy(accum)
        for entry in self.storage:
            next_tok = entry.next_token()
            for expansion in rules.get(next_tok, []):
                ret.add(TableEntry(next_tok, expansion, 0))
        return ret
    def add_predictions(self, rules):
        '''Add all "predictions" for the current table set'''
        self.storage = transitive_closure(self.storage, add_predictions_1)
    def shift(self, seen_token):
        alt_storage = set()
        for entry in self.storage:
            if entry.next_token() == seen_token:
                alt_storage.add()
    
def gen_table(rules, start_name):
    start_token = TableEntry.from_rule_and_name(rules, start_name)
    print(start_token)
    return start_token
    
    # First have 'Start' with 'dot' before it.
    #   - Look at token on right hand side of the 'dot'.
    #   - If is nonterminal, add the rules to generate that.
    # Second, shift the 'dot' in all rules for above table entry.
    #   - 

if __name__ == '__main__':
    import default_log_arg
    default_log_arg.do_default_logarg()
    with open('tutorial-grammar.txt') as infile:
        text = infile.read()
    all_rules = get_rules(text)
    logger.info('Initial rules: ' + str(all_rules))
    nonterminals = all_nonterminals(all_rules)
    logger.info('Nonterminals: ' + str(nonterminals))
    terminal = make_terminal_func(nonterminals)
    FIRST = first(all_rules)
    logger.info('FIRST: ' + str(FIRST))
    FOLLOW = follow(all_rules)
    logger.info('FOLLOW: ' + str(FOLLOW))
