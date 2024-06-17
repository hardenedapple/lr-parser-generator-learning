class State:
    def __init__(self):
        self.stack = []
        self.top = 0

def advance(st, next_symbol):
    while action_table[st.top][next_symbol](st):
        pass

def shift(to):
    def _shift_(st):
        print('shift {}'.format(to))
        st.stack.append(st.top)
        st.top = to
        return False
    return _shift_

def red(count, symbol):
    def _red_(st):
        for _ in range(count):
            st.top = st.stack.pop()
        print('reduce {}'.format(symbol))
        action_table[st.top][symbol](st)
        return True
    return _red_

def accept():
    def _accept_(st):
        st.top = st.stack.pop()
        print('accepted')
        return False
    return _accept_

action_table = [
    # s0
    {'Add':         shift(1),
     'Factor':      shift(2),
     'Term':        shift(3),
     '(':           shift(4),
     'name':        shift(5),
     'int':         shift(6)},
    # s1
    {'$':           accept(),
     '+':           shift(7)},
    # s2
    {'$':           red(1, 'Add'),
     '+':     red(1, 'Add'),
     ')':   red(1, 'Add'),
     '*':   shift(8)},
    # s3
    {'$':           red(1, 'Factor'),
     '*':     red(1, 'Factor'),
     '+':   red(1, 'Factor'),
     ')':   red(1, 'Factor')},
    # s4
    {'Add':           shift(9),
     'Factor':     shift(2),
     'Term':     shift(3),
     '(':     shift(4),
     'name':     shift(5),
     'int':   shift(6)},
    # s5
    {'$':           red(1, 'Term'),
     '+':     red(1, 'Term'),
     '*':   red(1, 'Term'),
     ')':   red(1, 'Term')},
    # s6
    {'$':           red(1, 'Term'),
     '+':     red(1, 'Term'),
     '*':   red(1, 'Term'),
     ')':   red(1, 'Term')},
    # s7
    {'Factor':           shift(11),
     'Term':     shift(3),
     '(':     shift(4),
     'name':     shift(5),
     'int':     shift(6),
    },
    # s8
    {'Term':     shift(10),
     '(':     shift(4),
     'name':     shift(5),
     'int':     shift(6),
    },
    # s9
    {')':           shift(12),
     '+':     shift(7),
    },
    # s10
    {'$':           red(3, 'Factor'),
     '*':           red(3, 'Factor'),
     '+':           red(3, 'Factor'),
     ')':           red(3, 'Factor'),
    },
    # s11
    {'$':           red(3, 'Add'),
     ')':           red(3, 'Add'),
     '+':           red(3, 'Add'),
     '*':           shift(8),
    },
    # s12
    {'$':           red(3, 'Term'),
     '*':           red(3, 'Term'),
     '+':           red(3, 'Term'),
     ')':           red(3, 'Term'),
    }]

if __name__ == '__main__':
    print('\nNext\n\n')
    st = State()
    advance(st, '(')
    advance(st, 'name')
    advance(st, '+')
    advance(st, 'int')
    advance(st, ')')
    advance(st, '$')

    print('\nNext\n\n')
    st = State()
    advance(st, 'name')
    advance(st, '+')
    advance(st, 'int')
    advance(st, '+')
    advance(st, 'int')
    advance(st, '*')
    advance(st, 'name')
    advance(st, '$')

    print('\nNext\n\n')
    st = State()
    advance(st, '(')
    advance(st, 'name')
    advance(st, '+')
    advance(st, 'int')
    advance(st, '+')
    advance(st, 'int')
    advance(st, '$')
