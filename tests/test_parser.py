import unittest

from pt_law_parser.expressions import Token, DocumentReference, ArticleReference, \
    NumberReference, LineReference
from pt_law_parser.parser import parse


class GeneralTestCase(unittest.TestCase):
    def _test(self, string, expected):
        result = parse(string, {'Decreto-Lei'}, {'Decretos-Leis'})
        self.assertEqual(string, result.as_str())

        for exp, index, in expected:
            self.assertEqual(result[index], exp)


class TestDocuments(GeneralTestCase):

    def test_single(self):
        self._test('Decreto-Lei nº 2/2013.',
                   [(DocumentReference('2/2013', Token('Decreto-Lei')), 4)])

        self._test('Decreto-Lei nº 2/2013/A,',
                   [(DocumentReference('2/2013/A', Token('Decreto-Lei')), 4)])

        self._test('Decreto-Lei nº 2-A/2013,',
                   [(DocumentReference('2-A/2013', Token('Decreto-Lei')), 4)])

    def test_many(self):
        self._test('Decretos-Leis n.os 1/2006, 2/2006, e 3/2006',
                   [(DocumentReference('1/2006', Token('Decretos-Leis')), 4),
                    (DocumentReference('2/2006', Token('Decretos-Leis')), 7),
                    (DocumentReference('3/2006', Token('Decretos-Leis')), 12)])

        self._test('Decretos-Leis n.os 1/2006, e 2/2006',
                   [(DocumentReference('1/2006', Token('Decretos-Leis')), 4),
                    (DocumentReference('2/2006', Token('Decretos-Leis')), 9)])

        self._test('Decretos-Leis n.os 64/2006, de 21 de março, '
                   '88/2006, de 23 de maio, e '
                   '196/2006, de 10 de outubro',
                   [(DocumentReference('64/2006', Token('Decretos-Leis')), 4),
                    (DocumentReference('88/2006', Token('Decretos-Leis')), 16),
                    (DocumentReference('196/2006', Token('Decretos-Leis')), 30)])


class TestArticles(GeneralTestCase):

    def test_single(self):
        self._test('no artigo 3º.', [(ArticleReference('3º'), 4)])

        self._test('no artigo 3º-A,', [(ArticleReference('3º-A'), 4)])

        self._test('no artigo anterior', [(ArticleReference('anterior'), 4)])

    def test_many(self):
        self._test('Os artigos 3º, 4º-A, 7º e 25º entram em vigor',
                   [(ArticleReference('3º'), 4),
                    (ArticleReference('4º-A'), 7),
                    (ArticleReference('7º'), 10),
                    (ArticleReference('25º'), 14)])

    def test_with_document(self):
        doc = DocumentReference('2/2013', Token('Decreto-Lei'))
        self._test('Os artigos 3º, 4º-A, 7º e 25º do Decreto-Lei 2/2013,',
                   [(ArticleReference('3º', doc), 4),
                    (ArticleReference('4º-A', doc), 7),
                    (ArticleReference('7º', doc), 10),
                    (ArticleReference('25º', doc), 14),
                    (doc, 20)])


class TestNumbers(GeneralTestCase):

    def test_single(self):
        self._test('no nº 2.', [(NumberReference('2'), 4)])
        self._test('no nº 2,', [(NumberReference('2'), 4)])
        self._test('no nº 2 ', [(NumberReference('2'), 4)])

    def test_many(self):
        self._test('Os n.os 1 e 3 deixam', [(NumberReference('1'), 4),
                                            (NumberReference('3'), 8)])

    def test_with_article(self):
        art = ArticleReference('seguinte')
        self._test('no nº 2 do artigo seguinte', [(NumberReference('2', art), 4)])

        self._test('nos n.os 2 e 3 do artigo seguinte',
                   [(NumberReference('2', art), 4),
                    (NumberReference('3', art), 8)])

        self._test('nos n.os 1, 2 e 3 do artigo seguinte',
                   [(NumberReference('1', art), 4),
                    (NumberReference('2', art), 7),
                    (NumberReference('3', art), 11)])

        art = ArticleReference('26º')
        self._test('no nº 2 do artigo 26º', [(NumberReference('2', art), 4)])

    def test_with_document(self):
        doc = DocumentReference('2/2013', Token('Decreto-Lei'))
        art = ArticleReference('26º', doc)
        self._test('no nº 2 do artigo 26º do Decreto-Lei 2/2013,',
                   [(NumberReference('2', art), 4)])


class TestLines(GeneralTestCase):

    def test_single(self):
        line = LineReference('f)')
        self._test('na alínea f).', [(line, 4)])
        self._test('na alínea f),', [(line, 4)])
        self._test('na alínea f) ', [(line, 4)])

    def test_many(self):
        expectation = [(LineReference('f)'), 4), (LineReference('g)'), 8)]

        self._test('nas alíneas f) e g).', expectation)
        self._test('nas alíneas f) e g) ', expectation)
        self._test('nas alíneas f) e g), como', expectation)

        expectation = [(LineReference('1)'), 4), (LineReference('5)'), 8)]

        self._test('nas alíneas 1) e 5).', expectation)
        self._test('nas alíneas 1) e 5) ', expectation)
        self._test('nas alíneas 1) e 5), como', expectation)

        expectation = [(LineReference('aa)'), 4), (LineReference('bb)'), 8)]

        self._test('nas alíneas aa) e bb).', expectation)
        self._test('nas alíneas aa) e bb) ', expectation)
        self._test('nas alíneas aa) e bb), como', expectation)

    def test_with_number(self):
        parent = NumberReference('4')
        self._test('na alínea f) do nº 4.',
                   [(LineReference('f)', parent), 4), (parent, 10)])

        parent = NumberReference('anterior')
        self._test('nas alíneas f) e g) do nº anterior.',
                   [(LineReference('f)', parent), 4),
                    (LineReference('g)', parent), 8), (parent, 14)])

        parent = ArticleReference('anterior')
        self._test('nas alíneas f) e g) do artigo anterior.',
                   [(LineReference('f)', parent), 4),
                    (LineReference('g)', parent), 8), (parent, 14)])

        parent = ArticleReference('26º')
        self._test('nas alíneas f) e g) do artigo 26º',
                   [(LineReference('f)', parent), 4),
                    (LineReference('g)', parent), 8), (parent, 14)])

    def test_with_document(self):
        document = DocumentReference('2/2013', Token('Decreto-Lei'))
        article = ArticleReference('26º', document)
        number = NumberReference('4', article)

        self._test('nas alíneas f) e g) do nº 4 do artigo 26º '
                   'do Decreto-Lei nº 2/2013',
                   [(LineReference('f)', number), 4),
                    (LineReference('g)', number), 8), (number, 14),
                    (article, 20), (document, 28)])
