import unittest

from pt_law_parser.expressions import Token, Separator, EndOfLine, Expression
from pt_law_parser.tokenizer import tokenize


class TestCase(unittest.TestCase):

    def test_tokenize(self):
        self.assertEqual(list(tokenize('the end', ' ')),
                         [Token('the'), Separator(' '),
                          Token('end'), EndOfLine()])

        self.assertEqual(list(tokenize('the end is', ' ', ('the end',))),
                         [Token('the end'), Separator(' '),
                          Token('is'), EndOfLine()])

    def test_keyterm_found(self):
        self.assertEqual(
            list(tokenize('this is the end of', ' ', ('the end',))),
            [Token('this'), Separator(' '),
             Token('is'), Separator(' '),
             Token('the end'),
             Separator(' '),
             Token('of'),
             EndOfLine()])

    def test_keyterm_not_found(self):
        self.assertEqual(list(tokenize('this is the foo of', ' ',
                                       ('the end',))),
                         [Token('this'),
                          Separator(' '),
                          Token('is'),
                          Separator(' '),
                          Token('the'),
                          Separator(' '),
                          Token('foo'),
                          Separator(' '),
                          Token('of'),
                          EndOfLine()])

    def test_similar_keyterms(self):
        expected = [Token('this'),
                    Separator(' '),
                    Token('is'),
                    Separator(' '),
                    Token('the'),
                    Separator(' '),
                    Token('foo'),
                    Separator(' '),
                    Token('of'),
                    EndOfLine()]

        self.assertEqual(list(tokenize('this is the foo of', ' ',
                                       ('the end', 'the bar'))),
                         expected)

        self.assertEqual(list(tokenize('this is the foo of', ' ',
                                       ('the foo is', 'foo is bad'))),
                         expected)

    def test_shifted_keyterms(self):
        self.assertEqual(list(tokenize('the foo is bad', ' ',
                                       ('the foo stay', 'foo is bad'))),
                         [Token('the'),
                          Separator(' '),
                          Token('foo is bad'),
                          EndOfLine()])

    def test_keyterm_in_word(self):
        """
        262.º with keyterm `.º` must return 262 and .º
        """
        self.assertEqual(
            list(tokenize(
                '262.º', ' ,',
                ('.º',))),
            [Token('262'), Token('.º'), EndOfLine()]
        )

        self.assertEqual(
            list(tokenize(
                '262.º-A', ' ,',
                ('.º',))),
            [Token('262'), Token('.º'), Token('-A'), EndOfLine()]
        )

    def test_real(self):
        self.assertEqual(
            list(tokenize(
                'no n.º 2 do artigo 26.º do Decreto-Lei 2/2013,', ' ,.',
                ('Decreto-Lei', 'Decretos-Leis', 'n.º', '.º', 'n.os'))),
            [Token('no'), Separator(' '), Token('n.º'), Separator(' '),
             Token('2'), Separator(' '), Token('do'), Separator(' '),
             Token('artigo'), Separator(' '), Token('26'),
             Token('.º'), Separator(' '), Token('do'),
             Separator(' '), Token('Decreto-Lei'), Separator(' '),
             Token('2/2013'), Separator(','), EndOfLine()]
        )
