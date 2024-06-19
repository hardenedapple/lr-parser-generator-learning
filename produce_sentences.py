import copy
import itertools as itt
import random
import string
import logging
from parse_grammar import get_rules
logger = logging.getLogger(__name__)

def terminal(sym, rules):
    return sym not in rules

def make_word(terminal):
    if terminal == 'name':
        return random.choice(string.ascii_lowercase[:7])
    if terminal == 'int':
        return str(random.randint(0, 40))
    return terminal

class NonTerm:
    '''Closure to call 'one_level_produce', but with repr for logging.'''
    def __init__(self, rules, nonterm):
        self.rules = rules
        self.nonterm = nonterm
    def __call__(self, depth):
        return one_level_produce(self.rules, self.nonterm, depth)
    def __repr__(self):
        return self.nonterm
    def __str__(self):
        return self.nonterm

def choose_min(productions, rules):
    def find_cost(p):
        return sum(int(terminal(sym, rules)) for sym in p)
    return min(productions, key=find_cost)

def one_level_produce(rules, nonterm, depth):
    logger.debug('one_level_produce -- {}'.format(nonterm))
    productions = rules[nonterm]
    if depth > 10:
        cur_choice = choose_min(productions, rules)
    else:
        cur_choice = random.choice(productions)
    logger.debug('choosing {}'.format(cur_choice))
    return [(x, make_word(x)) if terminal(x, rules) else
            NonTerm(rules, x) for x in cur_choice]

def produce(rules, nonterm, depth=0):
    '''A little convoluted in order to avoid recusion problems.
    Not only have a loop in order to avoid recursion, but also have to avoid
    the fact that when we have multiple nonterminals we are more likely to
    expand something into nonterminals.
    '''
    cur_level = one_level_produce(rules, nonterm, depth)
    depth += 1
    while True:
        adjusted = False
        logger.debug(' '.join(str(x) for x in cur_level))
        next_level = []
        for sym in cur_level:
            if callable(sym):
                next_level.extend(sym(depth))
                depth += 1
                adjusted = True
            else:
                next_level.append(sym)
        cur_level = next_level
        if not adjusted:
            break
    return cur_level

if __name__ == '__main__':
    import default_log_arg
    default_log_arg.do_default_logarg()
    with open('tutorial-grammar.txt') as infile:
        text = infile.read()
    all_rules = get_rules(text)
