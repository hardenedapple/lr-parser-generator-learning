import unittest
from parsing_from_text import parse_from_string

class TestManualExpressions(unittest.TestCase):
    def test_basic_addition(self):
        basic_exp = parse_from_string('x+y')
        known_ret = [':Add', [':Add', [':Factor', [':Term', 'x']]], '+', [':Factor', [':Term', 'y']]]
        self.assertEqual(basic_exp, known_ret)
        self.assertEqual(parse_from_string('x + y'), known_ret)
        self.assertEqual(parse_from_string('x+ y '), known_ret)
        self.assertEqual(parse_from_string('x+ y\n'), known_ret)

if __name__ == '__main__':
    unittest.main()
