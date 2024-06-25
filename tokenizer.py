'''
Tokens in the grammar that I'm handling:
    (, ), +, *, integers, names
'''
class Tokenizer:
    def __init__(self, on_output):
        self.on_output = on_output
        self.state = 'st_0'
        self.column = 1
        self.line   = 1
        self.pos = (1,1)
        self.inp = []

def st_0(tok, ch):
    '''Function for 'parse next char' when not in a word or integer'''
    if ch.isdigit():
        tok.pos = (tok.column, tok.line)
        tok.inp.append(ch)
        tok.state = 'st_digits'
    elif ch.isalpha() or ch == "_":
        tok.pos = (tok.column, tok.line)
        tok.inp.append(ch)
        tok.state = 'st_word'
    elif ch in ('+', '*', '(', ')', '-', '?'):
        # Single character tokens -- no matter what is around them
        tok.on_output(ch, ch,
                      (tok.column, tok.line), (tok.column+1, tok.line))
    elif ch == " " or ch == "\n" or ch == "\t" or ch == "\r":
        pass
    elif ch == '':
        tok.on_output('$', '',
                      (tok.column, tok.line), (tok.column+1, tok.line))
    else:
        tok.on_output('error', ch,
            (tok.column, tok.line), (tok.column+1, tok.line))

def st_word(tok, ch):
    if ch.isalpha() or ch == "_" or ch.isdigit():
        tok.inp.append(ch)
    else:
        tok.on_output('name', "".join(tok.inp),
            tok.pos, (tok.column+1, tok.line))
        tok.inp = []
        tok.state = 'st_0'
        st_0(tok, ch)

def st_digits(tok, ch):
    if ch.isdigit():
        tok.inp.append(ch)
        return
    if ch.isalpha() or ch == '_':
        tok.on_output('error: digits {} followed by'
                      ' char'.format(''.join(tok.inp)), ch,
                      (tok.column, tok.line), (tok.column+1, tok.line))
    else:
        tok.on_output('int', "".join(tok.inp),
            tok.pos, (tok.column+1, tok.line))
    tok.inp = []
    tok.state = 'st_0'
    st_0(tok, ch)

# Collects every 'st_' into a dictionary.
tokenize_n = dict((k,v) for k,v in globals().items()
    if k.startswith('st_'))

def tokenize(tok, ch):
    tokenize_n[tok.state](tok, ch)
    if ch == "\n":
        tok.line += 1
        tok.column = 1
    else:
        tok.column += 1

if __name__ == '__main__':
    import sys
    def print_on_output(item, text, start, stop):
        print((item, repr(text), start, stop))

    tok = Tokenizer(print_on_output)
    for ch in sys.stdin.read():
        tokenize(tok, ch)
