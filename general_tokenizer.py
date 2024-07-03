'''
Tokens in the grammar that I'm handling:
    (, ), +, *, integers, names
'''
# Read in first char
# - Find TokenType that this first char satisfies.
# - Switch to that "state".
# - Read in chars until next char is not in charset_remainder
# - At which point ...
#   - If char is whitespace, go back to "base" state.
#   - Otherwise, go back to "base" state, then switch according to this char.
#
# Need to "initialise" the code based on some rules read from grammar.
# Hence I think it seems sensible to use a class to store the rules.
# Don't need the class itself to do the generation etc though.
#
# Something interesting is that a tokenizer could be implemented as a
# relatively simple version of an LR parser.  TODO would be interesting to
# implement that approach in the future.

from dataclasses import dataclass, field

class TokenizerState:
    def __init__(self, on_output, name, charset_first, charset_remainder):
        self.name = name
        self.on_output = on_output
        self.charset_first = charset_first
        self.charset_remainder = charset_remainder
        self.inp = []
    def reset(self, ch):
        assert(ch in self.charset_first)
        self.inp = [ch]
    def consume(self, ch):
        if ch in self.charset_remainder:
            self.inp.append(ch)
            return True
        return False
    def finish(self, start_pos, end_pos):
        self.on_output(self.name, ''.join(self.inp), start_pos, end_pos)

def do_nothing(*args):
    pass
def make_nulling_state(charset):
    return TokenizerState(do_nothing, None, charset, charset)
def make_single_char_states(on_output, chars):
    return

# Thoughts on general approach:
#   - Current state takes character.
#     - If state accepts character then update internal data accordingly
#       and continue.
#     - If state does not accept character, then "finish" state (accept of some
#       sort) and change state according to character.

# `all_states` is a list TokenizerState values.
class Tokenizer:
    def __init__(self, all_states, on_end):
        self.on_end = on_end
        self.all_states = all_states
        assert(len(all_states) ==
               len(set(x.name for x in all_states)))
        assert(len(all_states) ==
               len(set(x.charset_first for x in all_states)))
        self.current_state = make_nulling_state(set())
        self.column = 1
        self.line   = 1
        self.pos = (1,1)
        self.inp = []

    def choose_state_for(self, ch):
        ret = [x for x in self.all_states if ch in x.charset_first]
        assert(len(ret) == 1)
        return ret[0]

    def update_position(self, ch):
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

    def eof(self):
        self.current_state.finish(self.pos, (self.column, self.line))
        self.on_end(self.pos, (self.column, self.line))
        return

    def consume_char(self, ch):
        maintain_state = self.current_state.consume(ch)
        if not maintain_state:
            # Using on_output to make things in the current
            self.current_state.finish(self.pos, (self.column, self.line))
            self.current_state = self.choose_state_for(ch)
            self.current_state.reset(ch)
            self.pos = (self.column, self.line)
        self.update_position(ch)

if __name__ == '__main__':
    import sys
    import string
    def print_on_output(item, text, start, stop):
        print((item, text, start, stop))
    word_state = TokenizerState(print_on_output, 'word',
                                string.ascii_letters + '_',
                                string.ascii_letters + '_')
    number_state = TokenizerState(print_on_output, 'digit', string.digits,
                                  string.digits)
    all_states = [TokenizerState(print_on_output, x, x, '')
                  for x in ('+', '*', '(', ')', '-')]
    all_states += [word_state, number_state]
    all_states += [make_nulling_state(string.whitespace)]
    tok = Tokenizer(all_states, lambda x, y: print_on_output('$', '', x, y))
    for ch in sys.stdin.read():
        tok.consume_char(ch)
    tok.eof()
