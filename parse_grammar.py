import collections

def split_strip(line):
    return [x.strip() for x in line.split()]

def single_rule(line):
    k, r = line.split('=')
    return (k.strip(), split_strip(r))

def get_rules(text):
    ret = collections.defaultdict(list)
    for line in text.splitlines():
        if line.startswith('//'):
            continue
        line = line.strip()
        if not line:
            continue
        k, r = single_rule(line)
        ret[k].append(r)
    return ret
