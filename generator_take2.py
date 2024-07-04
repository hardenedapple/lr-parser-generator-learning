# Now I know (more of) what I need to do, approaching this from first
# principles).
#
# What I need (for SLR):
#   - All itemsets (generate directly from the grammar)
#   - FIRST sets (help determine the FOLLOW set).
#   - FOLLOW sets (generate directly from grammar)
#     - This helps decide the action table.
#   - Action table
#     - Use the FOLLOW set to calculate this.
#
# N.b. for canonical LR(1) parsing, the itemsets are a bit more tied in with
# the FOLLOW set.  The first rule (that describes "program" or "total" or the
# like) has nothing after it and the other rules have something after them
# based on where they are "predicted" from.
# E.g.
#    Add   -> . Term + Term {$}
#    Term  -> . int {+}
# In this case FOLLOW(itemset, Term) == {+}
# We can have different itemsets based on the FOLLOW sets for different terms
# in canonical LR(1) parsing.
#
#
# General algorithm for building SLR action table:
#   - Read in grammar rules.
#   - Start from first rule
#     - N.b. how would one determine this?
#       Just whichever rule doesn't have its nonterminal in any other
#       generation rule?
#   - Generate all itemsets.
#     - Shift on each symbol in order to make each new itemset.
#     - Record which have been generated.
#     - Avoid reproducing duplicates.
#   - Generate FIRST sets.
#     - Only want terminals in this set.
#   - Generate FOLLOW sets.
#     - Again, only want terminals in this set.
#   - For each itemset, for each item in the itemset, find the next symbol.
#     That next symbol is either the next in the rule, or something in the
#     FOLLOW set for this rule.  If we see this symbol we should either shift
#     (if it's in the current rule) or reduce (if it's a FOLLOW because there
#     are no more symbols in the current rule).
#     - These are the actions for this itemset.
#
# Data structures I need (whether special or just combinations of existing
# ones):
#   - Itemset
#     - Containing an action table.
#     - Hashable (excluding action table) so that we can check for duplicates.
#   - Represent "EOF" as a token.
#   - FIRST set
#   - FOLLOW set (later to be associated with a specific itemset, but for now,
#     with SLR, independent).

from parse_grammar import get_rules, get_rules_and_tokens
import manual_tables
import enum
from dataclasses import dataclass
import collections
import itertools as itt
import logging
logger = logging.getLogger(__name__)

# Rules are a dictionary of nonterminal: [expansion, ...]
# Each expansion is the current List of expansions is all the possible expansions.
def transitive_closure_mutable(init, update):
    while update(init):
        pass
    return init

def make_terminal_func(nonterminals):
    def terminal(tok):
        return tok not in nonterminals
    return terminal

def all_nonterminals(rules):
    return set(rules.keys())

####### Finding Nullable symbols.

def known_nullable(sym, expansions, already_known):
    if sym in already_known:
        return True
    def nullable_gen(gen):
        return all(x in already_known for x in gen)
    return any(nullable_gen(x) for x in expansions)

def nullable_syms(rules):
    def update_nullable(verified_nullable):
        logger.debug('update_nullable: ' + str(verified_nullable))
        ret = False
        for key, val in rules.items():
            if key in verified_nullable:
                continue
            if known_nullable(key, val, verified_nullable):
                verified_nullable.add(key)
                ret = True
        return ret
    return transitive_closure_mutable(set(), update_nullable)
    
#######  FIRST set.
def first(rules, nullable):
    # At one point I was concerned that FIRST(x) could need FOLLOW to figure out.
    # I.e. when x is nullable.  I think this is not a problem since FIRST is only used in FOLLOW, so if I make sure to check for x being nullable when determining FOLLOW I shouldn't need to take it into account when defining FIRST.
    # Instead, FIRST just needs to find everything that *could* start a given nonterminal.  The possibility that a given nonterminal may expand to nothing doesn't need to be represented in this data structure.
    SymStore = collections.namedtuple('SymStore', ['terminals', 'nonterminals'])
    first_items = collections.defaultdict(lambda: SymStore(set(), set()))
    for key, val in rules.items():
        item = first_items[key]
        for gen in val:
            for sym in gen:
                toupdate = item.terminals if terminal(sym) else item.nonterminals
                toupdate.add(sym)
                if sym not in nullable:
                    break
    def update_first(current_first):
        ret = False
        logger.debug('update_first: ' + str(current_first))
        for key in rules:
            this_first = current_first[key]
            for nont in this_first.nonterminals:
                that_first = current_first[nont]
                if not this_first.terminals.issuperset(that_first.terminals):
                    ret = True
                    this_first.terminals.update(that_first.terminals)
        return ret
    finalised_first = transitive_closure_mutable(first_items, update_first)
    return {key: val.terminals for key, val in finalised_first.items()}

####### FOLLOW set
def follow(rules, first, nullable, known):
    SymStore = collections.namedtuple('SymStore', ['terminals', 'follow'])
    follow_items = {key: SymStore(set(), set()) for key in rules}
    for k, v in known.items():
        follow_items[k].terminals.update(v)
    for key, val in rules.items():
        for gen in val:
            update_list = []
            for sym in gen:
                for s in update_list:
                    item = follow_items[s]
                    if terminal(sym):
                        item.terminals.add(sym)
                    else:
                        item.terminals.update(first[sym])
                if terminal(sym):
                    update_list = []
                elif sym not in nullable:
                    update_list = [sym]
                else:
                    update_list.append(sym)
            # Above loop handles all up to last element, this handles
            # everything "active" at end of rule.
            for s in update_list:
                item = follow_items[s]
                item.follow.add(key)
    def update_follow(current_follow):
        logger.debug('update_follow: ' + str(current_follow))
        ret = False
        for key, this in current_follow.items():
            for chain in this.follow:
                that = current_follow[chain]
                if not this.terminals.issuperset(that.terminals):
                    ret = True
                    this.terminals.update(that.terminals)
        return ret
    finalised_follow = transitive_closure_mutable(follow_items, update_follow)
    return {k: v.terminals for k, v in finalised_follow.items()}
    
####### Itemsets
# Structure of an SLR itemset is:
#   - Sequence of items.
# Where each item is:
#   - Rule plus position
@dataclass(frozen=True)
class Prediction:
    key: str
    gen: tuple[str, ...]
    idx: int
    def next_sym(self):
        return self.gen[self.idx] if self.idx < len(self.gen) else None
    def shifted(self):
        assert(self.idx < len(self.gen))
        return Prediction(self.key, self.gen, self.idx+1)
    def __str__(self):
        return '{} -> {} . {}'.format(self.key,
                                      ' '.join(self.gen[:self.idx]),
                                      ' '.join(self.gen[self.idx:]))
@dataclass(frozen=True)
class ItemSet:
    predictions: frozenset[Prediction, ...]
    @classmethod
    def from_iterable(cls, it):
        return cls(frozenset(it))
    def __str__(self):
        return '\n'.join(sorted(str(x) for x in self.predictions))
    def __iter__(self):
        return iter(self.predictions)

def left_pad(text, padding):
    return '\n'.join(padding+x for x in text.splitlines())

class StateStore:
    def __init__(self, mapping, reduction_actions, shift_actions, accept_actions):
        self.state_to_num = mapping
        self.num_to_state = {v: k for k, v in mapping.items()}
        self.shift_actions = shift_actions
        self.reduction_actions = reduction_actions
        self.accept_actions = accept_actions
        assert(set(self.num_to_state.keys()) == set(range(len(mapping))))
    def __str__(self):
        chunks = [list() for _ in self.num_to_state]
        for k, v in self.num_to_state.items():
            chunks[k].append('{}:'.format(k))
            chunks[k].append(left_pad(str(v), '    '))
            if self.shift_actions[v]:
                chunks[k].append('  Shifts:')
                for sym, next_state in self.shift_actions[v].items():
                    chunks[k].append('    {}:  shift({})'.format(
                            sym, self.state_to_num[next_state]))
            if self.reduction_actions[v]:
                chunks[k].append('  Reductions:')
                for sym, pred in self.reduction_actions[v].items():
                    chunks[k].append('    {}:  reduce({})'.format(sym, pred))
            if self.accept_actions[v]:
                chunks[k].append('  Accept on:')
                for sym in self.accept_actions[v]:
                    chunks[k].append('    {}'.format(sym))
        return '\n'.join(itt.chain.from_iterable(chunks))

def extend_predictions(rules, predictions):
    '''Expand a kernel of an itemset into a full itemset.
    NOTE: This can lead to duplicates of the items in the kernel, but we assume
    that's handled by ItemSet making things unique.'''
    logger.debug('extending: ' + str(predictions))
    tohandle = [p.next_sym() for p in predictions]
    seen = set()
    while tohandle:
        logger.debug('tohandle:' + str(tohandle))
        logger.debug('seen:    ' + str(seen))
        sym = tohandle.pop()
        if sym in seen or sym is None:
            continue
        seen.add(sym)
        extra = [Prediction(sym, tuple(x), 0) for x in rules[sym]]
        predictions.extend(extra)
        tohandle.extend(x.next_sym() for x in extra)
    return predictions

def actions_for(predictions, root_term, follow):
    ret = collections.defaultdict(list)
    reductions = {}
    accepts = set()
    for p in predictions:
        sym = p.next_sym()
        if sym is None:
            for f in follow[p.key]:
                # Early assertion error on shift/reduce conflict.
                assert(f not in ret)
                # Assertion error on reduce/reduce conflict.
                assert(f not in reductions)
                if p.key == root_term:
                    accepts.add(f)
                else:
                    reductions[f] = p
            continue
        ret[sym].append(p.shifted())
    return reductions, ret, accepts

# N.b. I'm curious whether there is any way to determine where the start is
# automatically.
# Thoughts:
#   - Hash on kernels rather than entire states?
#     Should do essentially the same thing, but could save in "seen"
#     before expanding (saving a bit of work).
def itemlists(rules, root_term, follow):
    # Approach:
    #  1) Expand all implicit states from the beginning of root_term.
    #     - This gives the first itemlist.
    #  2) For each symbol in any "next" position:
    #     - Create the kernel of a new itemset.
    #     - Expand all implicit states.
    predictions = [Prediction(root_term, tuple(x), 0) for x in rules[root_term]]
    extend_predictions(rules, predictions)
    start = ItemSet.from_iterable(predictions)
    counter = 0
    seen = {}
    tohandle = [start]
    shift_actions = {}
    reduction_actions = {}
    accept_actions = {}
    while tohandle:
        s = tohandle.pop()
        if s in seen:
            continue
        seen[s] = counter
        counter += 1
        reductions, shifts, accepts = actions_for(s.predictions, root_term, follow)
        for sym in shifts:
            extend_predictions(rules, shifts[sym])
            toadd = ItemSet.from_iterable(shifts[sym])
            shifts[sym] = toadd
            if toadd not in seen:
                tohandle.append(toadd)
        # Assertion error on reduce/shift conflict.
        assert(not any(x in reductions for x in shifts))
        assert(not any(x in reductions for x in accepts))
        assert(not any(y in shifts for y in accepts))
        reduction_actions[s], shift_actions[s], accept_actions[s] = (
                reductions, shifts, accepts)
    return StateStore(seen, reduction_actions, shift_actions, accept_actions)

######### Using that action table to parse.
def convert_to_action_table(state_store, root_term):
    action_tables = [None]*len(state_store.num_to_state)
    for k, v in state_store.num_to_state.items():
        shifts = {sym: manual_tables.shift(state_store.state_to_num[next_state])
                  for sym, next_state in state_store.shift_actions[v].items()}
        reductions = {sym: manual_tables.red(len(p.gen), p.key)
                        for sym, p in state_store.reduction_actions[v].items()}
        accepts = {sym: manual_tables.accept() for sym in state_store.accept_actions[v]}
        assert(not any(x in shifts for x in reductions))
        assert(not any(x in accepts for x in reductions))
        assert(not any(y in shifts for y in accepts))
        actions = shifts
        actions.update(reductions)
        actions.update(accepts)
        action_tables[k] = actions
    assert(None not in action_tables)
    return action_tables

def generate_action_tables(grammar_filename):
    global terminal
    with open(grammar_filename) as infile:
        text = infile.read()
    all_rules = get_rules(text)
    logger.info('Initial rules: ' + str(all_rules))
    nullable = nullable_syms(all_rules)
    logger.info('Nullable: ' + str(nullable))
    nonterminals = all_nonterminals(all_rules)
    logger.info('Nonterminals: ' + str(nonterminals))
    terminal = make_terminal_func(nonterminals)
    FIRST = first(all_rules, nullable)
    logger.info('FIRST: ' + str(FIRST))
    FOLLOW = follow(all_rules, FIRST, nullable, {'Start': ['$']})
    logger.info('FOLLOW: ' + str(FOLLOW))
    states = itemlists(all_rules, 'Start', FOLLOW)
    logger.info('States: ' + str(states))
    return convert_to_action_table(states, 'Start')

def get_tokenizer(grammar_filename):
    with open(grammar_filename) as infile:
        text = infile.read()
    _, named_tokens, unnamed_tokens = get_rules_and_tokens(text)
    return parsing_from_text.ParametrisedTokenizer(named_tokens, unnamed_tokens)

def initialise_actions(grammar_filename):
    action_table = generate_action_tables(grammar_filename)
    manual_tables.initialise_actions(action_table)

if __name__ == '__main__':
    import pprint
    import sys
    import parsing_from_text
    import default_log_arg
    default_log_arg.do_default_logarg()
    text = sys.stdin.read()
    if text:
        initialise_actions('tutorial-grammar.txt')
        logger.info('action_tables: ' + pprint.pformat(manual_tables.action_table))
        parsed_expression = parsing_from_text.parse_from_string(text)
        pprint.pprint(parsed_expression)
    else:
        try:
            initialise_actions('slr_lr_grammar.txt')
        except AssertionError:
            pass
        else:
            assert(not 'Should have failed to generate grammar! (is not SLR)')
        initialise_actions('tutorial-grammar.txt')
        tokenizer = get_tokenizer('tutorial-grammar.txt')
        parsed_expression = parsing_from_text.general_parse_from_string(
                                'n * (4+5)*3 + somename', tokenizer)
        assert(parsed_expression ==
                    [[':Add',
                      [':Add',
                       [':Factor',
                        [':Factor',
                         [':Factor', [':Term', [':Minus'], 'n']],
                         '*',
                         [':Term',
                          [':Minus'],
                          '(',
                          [':Add',
                           [':Add', [':Factor', [':Term', [':Minus'], '4']]],
                           '+',
                           [':Factor', [':Term', [':Minus'], '5']]],
                          ')']],
                        '*',
                        [':Term', [':Minus'], '3']]],
                      '+',
                      [':Factor', [':Term', [':Minus'], 'somename']]]])

