import collections
import re
import logging
logger = logging.getLogger(__name__)

def split_strip(line):
    return [x.strip() for x in line.split()]

def is_grammar(line):
    return bool(re.match(r'^\w+ +=', line))
def single_rule(line):
    k, r = line.split('=')
    return (k.strip(), split_strip(r))

def is_token(line):
    return bool(re.match(r'^\w+ +:=', line))
def single_token(line):
    k, t = line.split(':=')
    startchars, followchars = t.split()
    return (k.strip(), (startchars.strip(), followchars.strip()))

def get_rules_and_tokens(text):
    logger.debug('Parsing:\n' + text)
    ret = collections.defaultdict(list)
    all_tokens = set()
    named_tokens = {}
    for line in text.splitlines():
        if line.startswith('//'):
            continue
        line = line.strip()
        if not line:
            continue
        if is_grammar(line):
            logger.debug('grammar line: {}'.format(line))
            k, r = single_rule(line)
            ret[k].append(r)
            all_tokens.update(r)
        elif is_token(line):
            k, t = single_token(line)
            assert(k not in named_tokens)
            named_tokens[k] = t
    logger.debug('named_tokens: {}'.format(str(named_tokens)))
    logger.debug('all_tokens:   {}'.format(str(all_tokens)))
    assert(all(x in all_tokens for x in named_tokens.keys()))
    assert(all(y in set(named_tokens.keys()).union(set(ret.keys()))
                for y in (x for x in all_tokens if len(x) > 1)))
    return ret, named_tokens, set(x for x in all_tokens
                                  if x not in named_tokens and x not in ret)

def get_rules(text):
    return get_rules_and_tokens(text)[0]

if __name__ == '__main__':
    import sys
    import pprint
    import default_log_arg
    default_log_arg.do_default_logarg()
    rules, named_tokens, unnamed_tokens = get_rules_and_tokens(sys.stdin.read())
    pprint.pprint(rules)
    pprint.pprint(tokens)
