import unittest
import operator
import random
from parsing_from_text import (parse_from_string, general_parse_from_string, ParametrisedTokenizer)
from parse_grammar import get_rules, get_rules_and_tokens
import itertools as itt
import manual_tables
import produce_sentences
import logging
logger = logging.getLogger(__name__)

def merge_sentence_as_string(sent):
    # N.b. All tokens can be directly after each other (i.e. without
    # whitespace) as far as the tokenizer is concerned -- *except* names being
    # directly after integers.
    # However, since we generate *valid* grammar, and a name is not allowed
    # directly after a digit, we don't need to worry about that for this
    # function.
    #   - For testing posibly bad tokens we may need to worry about this.
    #
    # N.b. including '' twice in order to increase possibility of no whitespace
    # in between tokens.
    def random_choices(spaces):
        while True:
            yield random.choice(spaces)
    all_tokens = map(operator.itemgetter(1), sent)
    spaces = (a+b for a,b in itt.product(['', '\n', '\t', ' ', ''], repeat=2))
    random_spaces = random_choices(list(spaces))
    return ''.join(itt.chain.from_iterable(zip(all_tokens, random_spaces)))

class TestManualExpressions(unittest.TestCase):
    # Probably not the best way to test because I'm testing that the hard-coded
    # rules below match the hard-coded decision tables in manual_tables.
    # However, since the hard-coded decision tables are hard-coded there's not
    # much else I can do except write down what I think I wrote.
    test_rules = '''
    Start  = Add

    Add    = Add + Factor
    Add    = Factor

    Factor = Factor * Term
    Factor = Term

    Term   = ( Add )
    Term   = name
    Term   = int

    name := abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ

    int := 0123456789 0123456789
    '''
    def setUp(self):
        manual_tables.initialise_actions(None)
    def test_basic(self):
        basic_exp = parse_from_string('x+y')
        known_ret = [[':Add', [':Add', [':Factor', [':Term', 'x']]], '+', [':Factor', [':Term', 'y']]]]
        self.assertEqual(basic_exp, known_ret)
        self.assertEqual(parse_from_string('x + y'), known_ret)
        self.assertEqual(parse_from_string('x+ y '), known_ret)
        self.assertEqual(parse_from_string('x+ y\n'), known_ret)
        known_ret = [[':Add', [':Factor', [':Term', 'x']]]]
        self.assertEqual(parse_from_string('x'), known_ret)
    def test_parser_accepts(self):
        rules, named_tokens, unnamed_tokens = get_rules_and_tokens(self.test_rules)
        generated_tokenizer = ParametrisedTokenizer(named_tokens, unnamed_tokens)
        all_keys = list(rules.keys())
        for _ in range(1000):
            gen_key = random.choice(all_keys)
            generated = produce_sentences.produce(rules, gen_key)
            st = manual_tables.State()
            for ty, text in generated:
                manual_tables.advance(st, ty, text)
            manual_tables.advance(st, '$', '')
            self.assertTrue(st.accepted_expressions)
            directly = st.accepted_expressions[0]
            text_expression = merge_sentence_as_string(generated)
            via_text = parse_from_string(text_expression)
            self.assertEqual(via_text, directly)
            via_text_generated_tokenizer = general_parse_from_string(
                            text_expression, generated_tokenizer)
            self.assertEqual(via_text_generated_tokenizer, directly)

if __name__ == '__main__':
    import default_log_arg
    default_log_arg.do_default_logarg()
    import sys
    sys.argv = [x for x in sys.argv if not x.startswith('--loglevel')]
    unittest.main()
