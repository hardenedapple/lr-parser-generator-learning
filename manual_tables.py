import pprint
import logging
logger = logging.getLogger(__name__)
class State:
    def __init__(self):
        self.accepted_expressions = []
        self.stack = []
        self.forest = []
        self.top = 0

def advance(st, next_symbol, value):
    while action_table[st.top][next_symbol](st, value):
        pass

def shift(to):
    def _shift_(st, value):
        logger.debug('shift {}'.format(to))
        st.stack.append(st.top)
        st.forest.append(value)
        st.top = to
        return False
    return _shift_

def red(count, symbol):
    name = symbol
    def _red_(st, _):
        args = []
        for _ in range(count):
            st.top = st.stack.pop()
            args.append(st.forest.pop())
        args.append(':' + name)
        args.reverse()
        logger.debug('reduce {}'.format(symbol))
        action_table[st.top][symbol](st, args)
        return True
    return _red_

def accept():
    def _accept_(st, _):
        st.top = st.stack.pop()
        st.accepted_expressions.append(st.forest)
        assert(len(st.accepted_expressions) == 1)
        logger.debug('Accepted: {}'.format(
                        pprint.pformat(st.accepted_expressions[0])))
        return False
    return _accept_

default_action_table = [
        # s0
        {'Add':     shift(1),
        'Factor':   shift(2),
        'Term':     shift(3),
        '(':        shift(4),
        'name':     shift(5),
        'int':      shift(6)
        },
        # s1
        {'$':       accept(),
        '+':        shift(7)
        },
        # s2
        {'$':       red(1,      'Add'),
        '+':        red(1,      'Add'),
        ')':        red(1,      'Add'),
        '*':        shift(8)
        },
        # s3
        {'$':       red(1,      'Factor'),
        '*':        red(1,      'Factor'),
        '+':        red(1,      'Factor'),
        ')':        red(1,      'Factor')
        },
        # s4
        {'Add':     shift(9),
        'Factor':   shift(2),
        'Term':     shift(3),
        '(':        shift(4),
        'name':     shift(5),
        'int':      shift(6)
        },
        # s5
        {'$':       red(1,      'Term'),
        '+':        red(1,      'Term'),
        '*':        red(1,      'Term'),
        ')':        red(1,      'Term')
        },
        # s6
        {'$':       red(1,      'Term'),
        '+':        red(1,      'Term'),
        '*':        red(1,      'Term'),
        ')':        red(1,      'Term')
        },
        # s7
        {'Factor':  shift(11),
        'Term':     shift(3),
        '(':        shift(4),
        'name':     shift(5),
        'int':      shift(6),
        },
        # s8
        {'Term':    shift(10),
        '(':        shift(4),
        'name':     shift(5),
        'int':      shift(6),
        },
        # s9
        {')':       shift(12),
        '+':        shift(7),
        },
        # s10
        {'$':       red(3,      'Factor'),
        '*':        red(3,      'Factor'),
        '+':        red(3,      'Factor'),
        ')':        red(3,      'Factor'),
        },
        # s11
        {'$':       red(3,      'Add'),
        ')':        red(3,      'Add'),
        '+':        red(3,      'Add'),
        '*':        shift(8),
        },
        # s12
        {'$':       red(3,      'Term'),
        '*':        red(3,      'Term'),
        '+':        red(3,      'Term'),
        ')':        red(3,      'Term'),
        }]

def initialise_actions(alt_actions):
    global action_table
    if alt_actions:
        action_table = alt_actions
    else:
        action_table = default_action_table

if __name__ == '__main__':
    import default_log_arg
    default_log_arg.do_default_logarg()
    print('\nNext\n\n')
    initialise_actions(None)
    st = State()
    advance(st, '(', '(')
    advance(st, 'name', 'x')
    advance(st, '+', '+')
    advance(st, 'int', '10')
    advance(st, ')', ')')
    advance(st, '$', '$')
    pprint.pprint(st.accepted_expressions)

    print('\nNext\n\n')
    st = State()
    advance(st, 'name', 'x')
    advance(st, '+', '+')
    advance(st, 'int', '13')
    advance(st, '+', '+')
    advance(st, 'int', '8')
    advance(st, '*', '*')
    advance(st, 'name', 'y')
    advance(st, '$', '$')
    pprint.pprint(st.accepted_expressions)

    # Should fail with unexpected `$`.
    print('\nNext\n\n')
    st = State()
    advance(st, '(', '(')
    advance(st, 'name', 'z')
    advance(st, '+', '+')
    advance(st, 'int', '9')
    advance(st, '+', '+')
    advance(st, 'int', '10')
    advance(st, '$', '$')
