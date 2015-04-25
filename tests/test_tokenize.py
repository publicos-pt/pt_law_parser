import unittest

from pt_law_parser.core.expressions import Token
from pt_law_parser.core.tokenizer import tokenize


class TestCase(unittest.TestCase):

    def test_basic(self):
        self.assertEqual(list(tokenize('the the', ' ')),
                         [Token('the'), Token(' '), Token('the')])

    def test_tokenize(self):
        self.assertEqual(list(tokenize('the end', ' ')),
                         [Token('the'), Token(' '),
                          Token('end')])

        self.assertEqual(list(tokenize('the end is', (' ', 'the end',))),
                         [Token('the end'), Token(' '),
                          Token('is')])

    def test_keyterm_found(self):
        self.assertEqual(
            list(tokenize('this is the end of', (' ', 'the end',))),
            [Token('this'), Token(' '),
             Token('is'), Token(' '),
             Token('the end'),
             Token(' '),
             Token('of')])

    def test_keyterm_not_found(self):
        self.assertEqual(list(tokenize('this is the foo of', (' ', 'the end',))),
                         [Token('this'),
                          Token(' '),
                          Token('is'),
                          Token(' '),
                          Token('the'),
                          Token(' '),
                          Token('foo'),
                          Token(' '),
                          Token('of')])

    def test_similar_keyterms(self):
        expected = [Token('this'),
                    Token(' '),
                    Token('is'),
                    Token(' '),
                    Token('the'),
                    Token(' '),
                    Token('foo'),
                    Token(' '),
                    Token('of')]

        self.assertEqual(list(tokenize('this is the foo of',
                                       (' ', 'the end', 'the bar'))),
                         expected)

        self.assertEqual(list(tokenize('this is the foo of',
                                       (' ', 'the foo is', 'foo is bad'))),
                         expected)

    def test_shifted_keyterms(self):
        self.assertEqual(list(tokenize('the foo is bad',
                                       (' ', 'the foo stay', 'foo is bad'))),
                         [Token('the'),
                          Token(' '),
                          Token('foo is bad')])

    def test_keyterm_in_word(self):
        """
        262.º with keyterm `.º` must return 262 and .º
        """
        self.assertEqual(
            list(tokenize('262.º', (' ', ',', '.º',))),
            [Token('262'), Token('.º')]
        )

        self.assertEqual(
            list(tokenize('262.º-A', (' ', ',', '.º',))),
            [Token('262'), Token('.º'), Token('-A')]
        )

    def test_keyterm_subset_of_keyterm(self):
        """
        When keyterm is a subset of the other, return other.
        """
        self.assertEqual(
            list(tokenize('Decreto-Lei', {'Decreto'})),
            [Token('Decreto'), Token('-Lei')])

        self.assertEqual(
            list(tokenize('Decreto-Lei', {'Decreto', 'Decreto-Lei'})),
            [Token('Decreto-Lei')])

        self.assertEqual(
            list(tokenize('Decreto-Barro', {'Decreto', 'Decreto-Lei'})),
            [Token('Decreto'), Token('-Barro')])

    def test_multiple_keyterms(self):
        self.assertEqual(
            list(tokenize('Decreto-Barros', {'Decreto', 'Decreto-Lei', '-Barro'})),
            [Token('Decreto'), Token('-Barro'), Token('s')])

    def test_keyterm_in_begin(self):
        self.assertEqual(
            list(tokenize('pre-foo-suf', ('pre', 'pre-foo-suf'))),
            [Token('pre-foo-suf')])

        self.assertEqual(
            list(tokenize('d-pre-foo-suf', ('pre', 'pre-foo-suf'))),
            [Token('d-'), Token('pre-foo-suf')])

    def test_keyterm_in_middle(self):
        self.assertEqual(
            list(tokenize('pre-foo-suf', ('foo', 'pre-foo-suf'))),
            [Token('pre-foo-suf')])

    def test_keyterm_in_end(self):
        self.assertEqual(
            list(tokenize('pre-foo-suf', ('pre-foo-suf', 'suf'))),
            [Token('pre-foo-suf')])

        self.assertEqual(
            list(tokenize('n.º 2', (' ', 'n.º', '.º'))),
            [Token('n.º'), Token(' '), Token('2')])

        self.assertEqual(
            list(tokenize('foo-bar', ('foo-bar', 'bar tal'))),
            [Token('foo-bar')])

    def test_keyterms_in_string_end(self):
        self.assertEqual(
            list(tokenize('the is', (' ', 'is solid', 'is black'))),
            [Token('the'), Token(' '), Token('is')])

    def test_real(self):
        self.assertEqual(
            list(tokenize(
                'no n.º 2 do artigo 26.º do Decreto-Lei 2/2013,',
                (' ', '.', ',', 'Decreto-Lei', 'Decretos-Leis',
                 'n.º', '.º', 'n.os'))),
            [Token('no'), Token(' '), Token('n.º'), Token(' '),
             Token('2'), Token(' '), Token('do'), Token(' '),
             Token('artigo'), Token(' '), Token('26'),
             Token('.º'), Token(' '), Token('do'),
             Token(' '), Token('Decreto-Lei'), Token(' '),
             Token('2/2013'), Token(',')]
        )
