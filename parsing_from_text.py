'''Combining tokenizer and parser to parse actual text'''
import tokenizer
import general_tokenizer
import manual_tables
import sys
import logging
logger = logging.getLogger(__name__)

def general_parse_from_string(inp, abstract_tokenizer):
    st = manual_tables.State()
    def do_advance(item, text, _, __):
        logger.debug('Calling advance with {}: {}'.format(item, text))
        manual_tables.advance(st, item, text)
    abstract_tokenizer.init(do_advance)
    for ch in inp:
        abstract_tokenizer.consume(ch)
    abstract_tokenizer.eof()
    assert(st.accepted_expressions)
    return st.accepted_expressions.pop()

class HardCodedTokenizer:
    def __init__(self):
        self.tok = None
    def init(self, advance):
        self.tok = tokenizer.Tokenizer(advance)
    def consume(self, ch):
        tokenizer.tokenize(self.tok, ch)
    def eof(self):
        tokenizer.tokenize(self.tok, '')

class ParametrisedTokenizer:
    def __init__(self, named_tokens, unnamed_tokens, ignorewhitespace=True):
        logger.debug('Calling ParametrizedTokenizer: {} {}'.format(
            named_tokens, unnamed_tokens))
        self.named_tokens, self.unnamed_tokens, self.ignorewhitespace = (
            named_tokens, unnamed_tokens, ignorewhitespace)
        self.tok = None
    def init(self, advance):
        tokenizer_states = general_tokenizer.states_from_grammar(
                        self.named_tokens, self.unnamed_tokens,
                        advance, self.ignorewhitespace)
        self.tok = general_tokenizer.Tokenizer(
                    tokenizer_states,
                    lambda x, y: advance('$', '', x, y))
    def consume(self, ch):
        self.tok.consume_char(ch)
    def eof(self):
        self.tok.eof()

def parse_from_string(inp):
    return general_parse_from_string(inp, HardCodedTokenizer())

if __name__ == '__main__':
    import default_log_arg
    default_log_arg.do_default_logarg()
    parsed_expression = parse_from_string(sys.stdin.read())
    import pprint
    pprint.pprint(parsed_expression)
