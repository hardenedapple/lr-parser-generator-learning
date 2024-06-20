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

from parse_grammar import get_rules
import collections
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
def follow(rules, first, nullable):
    SymStore = collections.namedtuple('SymStore', ['terminals', 'follow'])
    follow_items = collections.defaultdict(lambda: SymStore(set(), set()))
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
                if sym not in nullable:
                    update_list = [sym]
                else:
                    update_list.append(sym)
            # Above loop handles all up to last element.
            for s in update_list:
                item = follow_items[s]
                item.follow.add(key)
    def update_follow(current_follow):
        logger.debug('update_follow: ' + str(current_follow))
        ret = False
        for key in rules:
            this = current_follow[key]
            for chain in this.follow:
                that = current_follow[chain]
                if not this.terminals.issuperset(that.terminals):
                    ret = True
                    this.terminals.update(that.terminals)
        return ret
    finalised_follow = transitive_closure_mutable(follow_items, update_follow)
    return {k: v.terminals for k, v in finalised_follow.items()}

if __name__ == '__main__':
    import default_log_arg
    default_log_arg.do_default_logarg()
    with open('tutorial-grammar.txt') as infile:
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
    FOLLOW = follow(all_rules, FIRST, nullable)
    logger.info('FOLLOW: ' + str(FOLLOW))
