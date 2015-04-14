import unittest

from pt_law_parser.expressions import Token
from pt_law_parser.parser import parse


class TestDocuments(unittest.TestCase):

    def _test(self, string, parent, numbers):
        result = parse(string, {'Decreto-Lei'}, {'Decretos-Leis'})
        self.assertEqual(len(result['documents']), 1)
        self.assertEqual(result['documents'][0],
                         {'parent': parent, 'numbers': numbers})

    def test_single(self):
        self._test('Decreto-Lei nº 2/2013.',
                   Token('Decreto-Lei'), [Token('2/2013')])

        self._test('Decreto-Lei nº 2/2013/A,',
                   Token('Decreto-Lei'), [Token('2/2013/A')])

        self._test('Decreto-Lei nº 2-A/2013,',
                   Token('Decreto-Lei'), [Token('2-A/2013')])

    def test_many(self):
        self._test('Decretos-Leis n.os 1/2006, 2/2006, e 3/2006',
                   Token('Decretos-Leis'), [Token('1/2006'),
                                            Token('2/2006'),
                                            Token('3/2006')])

        self._test('Decretos-Leis n.os 1/2006, e 2/2006',
                   Token('Decretos-Leis'), [Token('1/2006'),
                                            Token('2/2006')])

        self._test('Decretos-Leis n.os 64/2006, de 21 de março, '
                   '88/2006, de 23 de maio, e '
                   '196/2006, de 10 de outubro',
                   Token('Decretos-Leis'), [Token('64/2006'),
                                            Token('88/2006'),
                                            Token('196/2006')])


class TestArticles(unittest.TestCase):

    def _test(self, string, parent, numbers):
        result = parse(string, {'Decreto-Lei'}, {'Decretos-Leis'})
        self.assertEqual(len(result['articles']), 1)
        self.assertEqual(result['articles'][0],
                         {'parent': parent, 'numbers': numbers})

    def test_single(self):
        self._test('dos SSMJ previstos no artigo 3º.',
                   None, [Token('3º')])

        self._test('dos SSMJ previstos no artigo 3º-A,',
                   None, [Token('3º-A')])

        self._test('dos SSMJ previstos no artigo anterior',
                   None, [Token('anterior')])

    def test_many(self):
        self._test('Os artigos 3º, 4º-A, 7º e 25º entram em vigor',
                   None, [Token('3º'), Token('4º-A'),
                          Token('7º'), Token('25º')])

    def test_with_document(self):
        self._test('Os artigos 3º, 4º-A, e 25º do Decreto-Lei 2/2013,',
                   {'parent': Token('Decreto-Lei'),
                    'numbers': [Token('2/2013')]},
                   [Token('3º'), Token('4º-A'), Token('25º')])


class TestNumbers(unittest.TestCase):

    def _test(self, string, parent, numbers):
        result = parse(string, {'Decreto-Lei'}, {'Decretos-Leis'})
        self.assertEqual(len(result['numbers']), 1)
        self.assertEqual({'parent': parent, 'numbers': numbers},
                         result['numbers'][0])

    def test_single(self):
        self._test('no nº 2.', None, [Token('2')])
        self._test('no nº 2,', None, [Token('2')])
        self._test('no nº 2 ', None, [Token('2')])

    def test_many(self):
        self._test('Os n.os 1 e 3 deixam', None, [Token('1'), Token('3')])

    def test_with_article(self):
        self._test('no nº 2 do artigo seguinte',
                   {'parent': None, 'numbers': [Token('seguinte')]},
                   [Token('2')])

        self._test('nos n.os 2 e 3 do artigo seguinte',
                   {'parent': None, 'numbers': [Token('seguinte')]},
                   [Token('2'), Token('3')])

        self._test('nos n.os 1, 2 e 3 do artigo seguinte',
                   {'parent': None, 'numbers': [Token('seguinte')]},
                   [Token('1'), Token('2'), Token('3')])

        self._test('no nº 2 do artigo 26º',
                   {'parent': None, 'numbers': [Token('26º')]},
                   [Token('2')])

    def test_with_document(self):
        self._test('no nº 2 do artigo 26º do Decreto-Lei 2/2013,',
                   {'parent': {'parent': Token('Decreto-Lei'),
                               'numbers': [Token('2/2013')]},
                    'numbers': [Token('26º')]},
                   [Token('2')])


class TestLines(unittest.TestCase):
    def _test(self, string, parent, numbers):
        result = parse(string, {'Decreto-Lei'}, {'Decretos-Leis'})
        self.assertEqual(len(result['lines']), 1)
        self.assertEqual({'parent': parent, 'numbers': numbers},
                         result['lines'][0])

    def test_single(self):
        self._test('na alínea f).', None, [Token('f)')])
        self._test('na alínea f),', None, [Token('f)')])
        self._test('na alínea f) ', None, [Token('f)')])

    def test_many(self):
        expectation = [Token('f)'), Token('g)')]

        self._test('referido na alíneas f) e g).', None, expectation)
        self._test('referido na alíneas f) e g) ', None, expectation)
        self._test('referido na alíneas f) e g), como', None, expectation)

        expectation = [Token('1)'), Token('5)')]

        self._test('referido na alíneas 1) e 5).', None, expectation)
        self._test('referido na alíneas 1) e 5) ', None, expectation)
        self._test('referido na alíneas 1) e 5), como', None, expectation)

        expectation = [Token('aa)'), Token('bb)')]

        self._test('referido na alíneas aa) e bb).', None, expectation)
        self._test('referido na alíneas aa) e bb) ', None, expectation)
        self._test('referido na alíneas aa) e bb), como', None, expectation)

    def test_with_number(self):

        self._test('referido na alínea f) do nº 4.',
                   {'parent': None, 'numbers': [Token('4')]},
                   [Token('f)')])

        self._test('referido nas alíneas f) e g) do nº anterior.',
                   {'parent': None, 'numbers': [Token('anterior')]},
                   [Token('f)'), Token('g)')])

        self._test('referido nas alíneas f) e g) do artigo anterior.',
                   {'parent': None, 'numbers': [Token('anterior')]},
                   [Token('f)'), Token('g)')])

        self._test('referido nas alíneas f) e g) do artigo 26º',
                   {'parent': None, 'numbers': [Token('26º')]},
                   [Token('f)'), Token('g)')])

    def test_with_document(self):
        self._test('referido nas alíneas f) e g) do nº 4 do artigo 26º '
                   'do Decreto-Lei nº 2/2013',
                   {'parent': {'parent': {'parent': Token('Decreto-Lei'),
                                          'numbers': [Token('2/2013')]},
                               'numbers': [Token('26º')]},
                    'numbers': [Token('4')]},
                   [Token('f)'), Token('g)')])
