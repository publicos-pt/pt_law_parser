import unittest

from pt_law_parser.tokenizer import Token, Separator, EndOfString, tokenize


class TestCase(unittest.TestCase):

    def test_tokenize(self):
        self.assertEqual(list(tokenize('the end', ' ')),
                         [Token('the', 0), Separator(' ', 3),
                          Token('end', 4), EndOfString('', 7)])

        self.assertEqual(list(tokenize('the end is', ' ', ('the end',))),
                         [Token('the end', 0), Separator(' ', 7),
                          Token('is', 8), EndOfString('', 10)])

    def test_keyterm_found(self):
        self.assertEqual(
            list(tokenize('this is the end of', ' ', ('the end',))),
            [Token('this', 0), Separator(' ', 4),
             Token('is', 5), Separator(' ', 7),
             Token('the end', 8),
             Separator(' ', 15),
             Token('of', 16),
             EndOfString('', 18)])

    def test_keyterm_not_found(self):
        self.assertEqual(list(tokenize('this is the foo of', ' ',
                                       ('the end',))),
                         [Token('this', 0),
                          Separator(' ', 4),
                          Token('is', 5),
                          Separator(' ', 7),
                          Token('the', 8),
                          Separator(' ', 11),
                          Token('foo', 12),
                          Separator(' ', 15),
                          Token('of', 16),
                          EndOfString('', 18)])

    def test_similar_keyterms(self):
        expected = [Token('this', 0),
                    Separator(' ', 4),
                    Token('is', 5),
                    Separator(' ', 7),
                    Token('the', 8),
                    Separator(' ', 11),
                    Token('foo', 12),
                    Separator(' ', 15),
                    Token('of', 16),
                    EndOfString('', 18)]

        self.assertEqual(list(tokenize('this is the foo of', ' ',
                                       ('the end', 'the bar'))),
                         expected)

        self.assertEqual(list(tokenize('this is the foo of', ' ',
                                       ('the foo is', 'foo is bad'))),
                         expected)

    def test_shifted_keyterms(self):
        self.assertEqual(list(tokenize('the foo is bad', ' ',
                                       ('the foo stay', 'foo is bad'))),
                         [Token('the', 0),
                          Separator(' ', 3),
                          Token('foo is bad', 4),
                          EndOfString('', 14)])

    def test_keyterm_in_word(self):
        """
        262.º with keyterm `.º` must return 262 and .º
        """
        self.assertEqual(
            list(tokenize(
                '262.º', ' ,',
                ('.º',))),
            [Token('262', 0), Token('.º', 3), EndOfString('', 5)]
        )

        self.assertEqual(
            list(tokenize(
                '262.º-A', ' ,',
                ('.º',))),
            [Token('262', 0), Token('.º', 3), Token('-A', 5), EndOfString('', 7)]
        )

    def test_real(self):
        self.assertEqual(
            list(tokenize(
                'no n.º 2 do artigo 26.º do Decreto-Lei 2/2013,', ' ,.',
                ('Decreto-Lei', 'Decretos-Leis', 'n.º', '.º', 'n.os'))),
            [Token('no', 0), Separator(' ', 2), Token('n.º', 3), Separator(' ', 6),
             Token('2', 7), Separator(' ', 8), Token('do', 9), Separator(' ', 11),
             Token('artigo', 12), Separator(' ', 18), Token('26', 19),
             Token('.º', 21), Separator(' ', 23), Token('do', 24),
             Separator(' ', 26), Token('Decreto-Lei', 27), Separator(' ', 38),
             Token('2/2013', 39), Separator(',', 45), EndOfString('', 46)]
        )
