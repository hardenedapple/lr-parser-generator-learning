import sys
import enum
import collections
import copy

def split_strip(line):
    return [x.strip() for x in line.split()]

def single_rule(line):
    k, r = line.split('=')
    return (k.strip(), split_strip(r))

def get_rules(text):
    ret = collections.defaultdict(list)
    for line in text.splitlines():
        if line.startswith('//'):
            continue
        line = line.strip()
        if not line:
            continue
        k, r = single_rule(line)
        assert(r)
        ret[k].append(r)
    return ret

class SpecialTok(enum.Enum):
    EOL = 'EOL'

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
            for s in start_token:
                ret[nt].update(accum[s])
        return ret
    return first_callback

def first(rules):
    prev_mapping = {}
    nts = all_nonterminals(rules)
    cur_mapping = {nt: first_from_rules(nt, rules) for nt in nts}
    start_token = {}
    for nt in nts:
        start_token[nt] = [other for other in nts
            if any(r[0] == nt for r in rules[other])]
    return transitive_closure(cur_mapping, make_first_callback(start_token))

def followed_by_in_rule(item, rule):
    ret = set()
    for idx, tok in enumerate(rule):
        if tok == item:
            if idx+1 == len(rule):
                ret.add(SpecialTok.EOL)
            elif terminal(rule[idx+1]):
                ret.add(rule[idx + 1])
    return ret

def followed_by(item, rules):
    ret = set()
    for v in rules.values():
        for r in v:
            ret.update(followed_by_in_rule(item, r))
    return ret

def make_followed_by_callback(ends_token):
    def followed_by_callback(accum):
        ret = copy.deepcopy(accum)
        for nt in accum:
            for e in ends_token[nt]:
                ret[nt].update(accum[e])
        return ret
    return followed_by_callback

def follow(rules):
    prev_mapping = {}
    nts = all_nonterminals(rules)
    cur_mapping = {nt : followed_by(nt, rules) for nt in nts}
    ends_token = {}
    for nt in nts:
        ends_token[nt] = [other for other in nts
             if any(r[-1] == nt for r in rules[other])]
    return transitive_closure(cur_mapping, make_followed_by_callback(ends_token))

if __name__ == '__main__':
    with open('tutorial-grammar.txt') as infile:
        text = infile.read()
    all_rules = get_rules(text)
    nonterminals = all_nonterminals(all_rules)
    terminal = make_terminal_func(nonterminals)
    FOLLOW = follow(all_rules)
    FIRST = first(all_rules)
