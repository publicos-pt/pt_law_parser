import unittest

from pt_law_parser.tokenizer import parse_string, Token


class TestDocumentsParser(unittest.TestCase):

    def _test(self, string, type_name, numbers):
        result = parse_string(string, {'Decreto-Lei'}, {'Decretos-Leis'})
        self.assertEqual(len(result['documents']), 1)
        self.assertEqual(result['documents'][0],
                         {'type_name': type_name, 'numbers': numbers})

    def test_single(self):
        self._test('Decreto-Lei nº 2/2013.',
                   Token('Decreto-Lei', 0), [Token('2/2013', 15)])

        self._test('Decreto-Lei nº 2/2013/A,',
                   Token('Decreto-Lei', 0), [Token('2/2013/A', 15)])

        self._test('Decreto-Lei nº 2-A/2013,',
                   Token('Decreto-Lei', 0), [Token('2-A/2013', 15)])

    def test_many(self):
        self._test('Decretos-Leis n.os 1/2006, 2/2006, e 3/2006',
                   Token('Decretos-Leis', 0), [Token('1/2006', 19),
                                               Token('2/2006', 27),
                                               Token('3/2006', 37)])

        self._test('Decretos-Leis n.os 1/2006, e 2/2006',
                   Token('Decretos-Leis', 0), [Token('1/2006', 19),
                                               Token('2/2006', 29)])

        self._test('Decretos-Leis n.os 64/2006, de 21 de março, '
                   '88/2006, de 23 de maio, e '
                   '196/2006, de 10 de outubro',
                   Token('Decretos-Leis', 0), [Token('64/2006', 19),
                                               Token('88/2006', 44),
                                               Token('196/2006', 70)])


class TestArticlesParser(unittest.TestCase):

    def _test(self, string, document, numbers):
        result = parse_string(string, {'Decreto-Lei'}, {'Decretos-Leis'})
        self.assertEqual(len(result['articles']), 1)
        self.assertEqual(result['articles'][0],
                         {'document': document, 'numbers': numbers})

    def test_single(self):
        self._test('dos SSMJ previstos no artigo 3º.',
                   None, [Token('3º', 29)])

        self._test('dos SSMJ previstos no artigo 3º-A,',
                   None, [Token('3º-A', 29)])

        self._test('dos SSMJ previstos no artigo anterior',
                   None, [Token('anterior', 29)])

    def test_many(self):
        self._test('Os artigos 3º, 4º-A, 7º e 25º entram em vigor',
                   None, [Token('3º', 11), Token('4º-A', 15),
                          Token('7º', 21), Token('25º', 26)])

    def test_with_document(self):
        self._test('Os artigos 3º, 4º-A, e 25º do Decreto-Lei 2/2013,',
                   {'type_name': Token('Decreto-Lei', 30),
                    'numbers': [Token('2/2013', 42)]},
                   [Token('3º', 11), Token('4º-A', 15), Token('25º', 23)])


class TestNumbersParser(unittest.TestCase):

    def _test(self, string, article, numbers):
        result = parse_string(string, {'Decreto-Lei'}, {'Decretos-Leis'})
        self.assertEqual(len(result['numbers']), 1)
        self.assertEqual({'article': article, 'numbers': numbers},
                         result['numbers'][0])

    def test_single(self):
        self._test('no nº 2.', None, [Token('2', 6)])
        self._test('no nº 2,', None, [Token('2', 6)])
        self._test('no nº 2 ', None, [Token('2', 6)])

    def test_many(self):
        self._test('Os n.os 1 e 3 deixam', None, [Token('1', 8), Token('3', 12)])

    def test_with_article(self):
        self._test('no nº 2 do artigo seguinte',
                   {'document': None, 'numbers': [Token('seguinte', 18)]},
                   [Token('2', 6)])

        self._test('nos n.os 2 e 3 do artigo seguinte',
                   {'document': None, 'numbers': [Token('seguinte', 25)]},
                   [Token('2', 9), Token('3', 13)])

        self._test('nos n.os 1, 2 e 3 do artigo seguinte',
                   {'document': None, 'numbers': [Token('seguinte', 28)]},
                   [Token('1', 9), Token('2', 12), Token('3', 16)])

        self._test('no nº 2 do artigo 26º',
                   {'document': None, 'numbers': [Token('26º', 18)]},
                   [Token('2', 6)])

    def test_with_document(self):
        self._test('no nº 2 do artigo 26º do Decreto-Lei 2/2013,',
                   {'document': {'type_name': Token('Decreto-Lei', 25),
                                 'numbers': [Token('2/2013', 37)]},
                    'numbers': [Token('26º', 18)]},
                   [Token('2', 6)])


class TestLines(unittest.TestCase):
    def _test(self, string, parent, lines):
        result = parse_string(string, {'Decreto-Lei'}, {'Decretos-Leis'})
        self.assertEqual(len(result['lines']), 1)
        self.assertEqual({'parent': parent, 'lines': lines},
                         result['lines'][0])

    def test_single(self):
        self._test('na alínea f).', None, [Token('f)', 10)])
        self._test('na alínea f),', None, [Token('f)', 10)])
        self._test('na alínea f) ', None, [Token('f)', 10)])

    def test_multiple(self):
        expectation = [Token('f)', 20), Token('g)', 25)]

        self._test('referido na alíneas f) e g).', None, expectation)
        self._test('referido na alíneas f) e g) ', None, expectation)
        self._test('referido na alíneas f) e g), como', None, expectation)

        expectation = [Token('1)', 20), Token('5)', 25)]

        self._test('referido na alíneas 1) e 5).', None, expectation)
        self._test('referido na alíneas 1) e 5) ', None, expectation)
        self._test('referido na alíneas 1) e 5), como', None, expectation)

        expectation = [Token('aa)', 20), Token('bb)', 26)]

        self._test('referido na alíneas aa) e bb).', None, expectation)
        self._test('referido na alíneas aa) e bb) ', None, expectation)
        self._test('referido na alíneas aa) e bb), como', None, expectation)

    def test_with_number(self):

        self._test('referido na alínea f) do nº 4.',
                   {'article': None, 'numbers': [Token('4', 28)]},
                   [Token('f)', 19)])

        self._test('referido nas alíneas f) e g) do nº anterior.',
                   {'article': None, 'numbers': [Token('anterior', 35)]},
                   [Token('f)', 21), Token('g)', 26)])

        self._test('referido nas alíneas f) e g) do artigo anterior.',
                   {'document': None, 'numbers': [Token('anterior', 39)]},
                   [Token('f)', 21), Token('g)', 26)])

        self._test('referido nas alíneas f) e g) do artigo 26º',
                   {'document': None, 'numbers': [Token('26º', 39)]},
                   [Token('f)', 21), Token('g)', 26)])

    def test_with_document(self):
        self._test('referido nas alíneas f) e g) do nº 4 do artigo 26º '
                   'do Decreto-Lei nº 2/2013',
                   {'article': {'document': {'type_name': Token('Decreto-Lei', 54),
                                             'numbers': [Token('2/2013', 69)]},
                                'numbers': [Token('26º', 47)]},
                    'numbers': [Token('4', 35)]},
                   [Token('f)', 21), Token('g)', 26)])
