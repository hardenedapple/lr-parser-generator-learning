'''Combining tokenizer and parser to parse actual text'''
import tokenizer
import manual_tables
import sys
import logging
logger = logging.getLogger(__name__)

def parse_from_string(inp):
    st = manual_tables.State()
    def do_advance(item, text, _, __):
        logger.debug('Calling advance with:' + item + text)
        manual_tables.advance(st, item, text)
    tok = tokenizer.Tokenizer(do_advance)
    for ch in inp:
        tokenizer.tokenize(tok, ch)
    tokenizer.tokenize(tok, '')
    assert(st.accepted_expressions)
    return st.accepted_expressions.pop()

if __name__ == '__main__':
    import default_log_arg
    default_log_arg.do_default_logarg()
    parsed_expression = parse_from_string(sys.stdin.read())
    import pprint
    pprint.pprint(parsed_expression)
