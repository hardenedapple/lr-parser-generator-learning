import generator_take2
from parsing_from_text import parse_from_string
import pickle
import pprint
import difflib

# TODO:
#   - Implement nice "diff" of objects.

def get_current(filename):
    answers = {}
    with open('accepted-testcases.txt') as infile:
        for line in infile:
            answers[line] = parse_from_string(line)
    return answers

def accept_current(infilename, outfilename):
    with open(outfilename, 'wb') as outfile:
        pickle.dump(get_current(infilename), outfile)

def test_no_change(infilename, outfilename):
    with open(outfilename, 'rb') as infile:
        orig_answers = pickle.load(infile)
    cur_answers = get_current(infilename)
    differences = {}
    for k, v in cur_answers.items():
        orig = orig_answers.get(k, [])
        if orig != v:
            differences[k] = (orig, v)
    return differences

def main():
    generator_take2.initialise_actions('tutorial-grammar.txt')
    infilename = 'accepted-testcases.txt'
    outfilename = 'accepted-outputs.pickle'
    diffs = test_no_change(infilename, outfilename)
    for k, (orig, new) in diffs.items():
        orig_pretty = pprint.pformat(orig)
        new_pretty = pprint.pformat(new)
        print('Diff for output "{}"'.format(k))
        print('\n'.join(difflib.context_diff(orig_pretty.splitlines(),
                                           new_pretty.splitlines(), 
                                           lineterm='')))

if __name__ == '__main__':
    main()
