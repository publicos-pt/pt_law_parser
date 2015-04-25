import unittest

from pt_law_parser.core.expressions import Token, DocumentReference, ArticleReference, \
    NumberReference, LineReference, Article, Number, Line
from pt_law_parser.core import parser
from pt_law_parser.core.parser import ObserverManager
from pt_law_parser.core.observers import DocumentsObserver, NumbersObserver, \
    LineObserver, ArticlesObserver


class GeneralTestCase(unittest.TestCase):
    def _test(self, string, managers, expected):
        result = parser.parse(string, managers, {' ', '.', ',', '\n', 'n.os'})
        self.assertEqual(string, result.as_str())

        for exp, index, in expected:
            self.assertEqual(result[index], exp)


class TestDocuments(GeneralTestCase):

    def test_single(self):
        managers = [ObserverManager({'Decreto-Lei': DocumentsObserver})]

        self._test('Decreto-Lei nº 2/2013.', managers,
                   [(DocumentReference('2/2013', Token('Decreto-Lei')), 4)])

        self._test('Decreto-Lei nº 2/2013/A,', managers,
                   [(DocumentReference('2/2013/A', Token('Decreto-Lei')), 4)])

        self._test('Decreto-Lei nº 2-A/2013,', managers,
                   [(DocumentReference('2-A/2013', Token('Decreto-Lei')), 4)])

    def test_many(self):
        managers = [ObserverManager({'Decretos-Leis': DocumentsObserver})]

        self._test('Decretos-Leis n.os 1/2006, 2/2006, e 3/2006', managers,
                   [(DocumentReference('1/2006', Token('Decretos-Leis')), 4),
                    (DocumentReference('2/2006', Token('Decretos-Leis')), 7),
                    (DocumentReference('3/2006', Token('Decretos-Leis')), 12)])

        self._test('Decretos-Leis n.os 1/2006, e 2/2006', managers,
                   [(DocumentReference('1/2006', Token('Decretos-Leis')), 4),
                    (DocumentReference('2/2006', Token('Decretos-Leis')), 9)])

        self._test('Decretos-Leis n.os 64/2006, de 21 de março, '
                   '88/2006, de 23 de maio, e '
                   '196/2006, de 10 de outubro', managers,
                   [(DocumentReference('64/2006', Token('Decretos-Leis')), 4),
                    (DocumentReference('88/2006', Token('Decretos-Leis')), 16),
                    (DocumentReference('196/2006', Token('Decretos-Leis')), 30)])

    def test_many_separated(self):

        managers = [ObserverManager({'foo': DocumentsObserver,
                                     'bar': DocumentsObserver})]

        string = 'foo 1/1. bar 2/1'
        expected = [(DocumentReference('1/1', Token('foo')), 2),
                    (DocumentReference('2/1', Token('bar')), 7)]

        self._test(string, managers, expected)

        string = 'foo 1/1 bar 2/1'
        expected = [(DocumentReference('1/1', Token('foo')), 2),
                    (DocumentReference('2/1', Token('bar')), 6)]

        self._test(string, managers, expected)


class TestArticles(GeneralTestCase):

    def test_single(self):
        managers = [ObserverManager({'artigo': ArticlesObserver})]

        self._test('no artigo 3º.', managers, [(ArticleReference('3º'), 4)])

        self._test('no artigo 3º-A,', managers, [(ArticleReference('3º-A'), 4)])

        self._test('no artigo anterior', managers,
                   [(ArticleReference('anterior'), 4)])

    def test_many(self):

        managers = [ObserverManager({'artigo': ArticlesObserver,
                                     'artigos': ArticlesObserver})]

        self._test('Os artigos 3º, 4º-A, 7º e 25º entram em vigor', managers,
                   [(ArticleReference('3º'), 4),
                    (ArticleReference('4º-A'), 7),
                    (ArticleReference('7º'), 10),
                    (ArticleReference('25º'), 14)])

    def test_with_document(self):

        managers = [ObserverManager({'Decreto-Lei': DocumentsObserver}),
                    ObserverManager({'artigos': ArticlesObserver})]

        doc = DocumentReference('2/2013', Token('Decreto-Lei'))
        self._test('Os artigos 3º, 4º-A, 7º e 25º do Decreto-Lei 2/2013,',
                   managers,
                   [(ArticleReference('3º', doc), 4),
                    (ArticleReference('4º-A', doc), 7),
                    (ArticleReference('7º', doc), 10),
                    (ArticleReference('25º', doc), 14),
                    (doc, 20)])


class TestNumbers(GeneralTestCase):

    def test_single(self):
        managers = [ObserverManager({'nº': NumbersObserver})]

        self._test('no nº 2.', managers, [(NumberReference('2'), 4)])
        self._test('no nº 2,', managers, [(NumberReference('2'), 4)])
        self._test('no nº 2 ', managers, [(NumberReference('2'), 4)])

    def test_many(self):
        managers = [ObserverManager({'n.os': NumbersObserver})]

        self._test('Os n.os 1 e 3 deixam', managers, [(NumberReference('1'), 4),
                                                      (NumberReference('3'), 8)])

    def test_with_article(self):
        managers = [ObserverManager({'artigo': ArticlesObserver}),
                    ObserverManager({'nº': NumbersObserver,
                                     'n.os': NumbersObserver})]

        art = ArticleReference('seguinte')
        self._test('no nº 2 do artigo seguinte', managers,
                   [(art, 10), (NumberReference('2', art), 4)])

        self._test('nos n.os 2 e 3 do artigo seguinte', managers,
                   [(NumberReference('2', art), 4),
                    (NumberReference('3', art), 8)])

        self._test('nos n.os 1, 2 e 3 do artigo seguinte', managers,
                   [(NumberReference('1', art), 4),
                    (NumberReference('2', art), 7),
                    (NumberReference('3', art), 11)])

        art = ArticleReference('26º')
        self._test('no nº 2 do artigo 26º', managers,
                   [(NumberReference('2', art), 4)])

    def test_with_document(self):
        managers = [ObserverManager({'Decreto-Lei': DocumentsObserver}),
                    ObserverManager({'artigo': ArticlesObserver}),
                    ObserverManager({'nº': NumbersObserver,
                                     'n.os': NumbersObserver})]

        doc = DocumentReference('2/2013', Token('Decreto-Lei'))
        art = ArticleReference('26º', doc)
        self._test('no nº 2 do artigo 26º do Decreto-Lei 2/2013,',
                   managers, [(doc, 16), (art, 10),
                              (NumberReference('2', art), 4)])


class TestLines(GeneralTestCase):

    def test_single(self):
        managers = [ObserverManager({'alínea': LineObserver})]

        line = LineReference('f)')
        self._test('na alínea f).', managers, [(line, 4)])
        self._test('na alínea f),', managers, [(line, 4)])
        self._test('na alínea f) ', managers, [(line, 4)])

    def test_many(self):
        managers = [ObserverManager({'alíneas': LineObserver})]

        expectation = [(LineReference('f)'), 4), (LineReference('g)'), 8)]

        self._test('nas alíneas f) e g).', managers, expectation)
        self._test('nas alíneas f) e g) ', managers, expectation)
        self._test('nas alíneas f) e g), como', managers, expectation)

        expectation = [(LineReference('1)'), 4), (LineReference('5)'), 8)]

        self._test('nas alíneas 1) e 5).', managers, expectation)
        self._test('nas alíneas 1) e 5) ', managers, expectation)
        self._test('nas alíneas 1) e 5), como', managers, expectation)

        expectation = [(LineReference('aa)'), 4), (LineReference('bb)'), 8)]

        self._test('nas alíneas aa) e bb).', managers, expectation)
        self._test('nas alíneas aa) e bb) ', managers, expectation)
        self._test('nas alíneas aa) e bb), como', managers, expectation)

    def test_with_parent(self):
        managers = [ObserverManager({'artigo': ArticlesObserver}),
                    ObserverManager({'nº': NumbersObserver}),
                    ObserverManager({'alíneas': LineObserver,
                                     'alínea': LineObserver})]

        parent = NumberReference('4')
        self._test('na alínea f) do nº 4.', managers,
                   [(LineReference('f)', parent), 4), (parent, 10)])

        parent = NumberReference('anterior')
        self._test('nas alíneas f) e g) do nº anterior.', managers,
                   [(parent, 14), (LineReference('f)', parent), 4),
                    (LineReference('g)', parent), 8)])

        parent = ArticleReference('anterior')
        self._test('nas alíneas f) e g) do artigo anterior.', managers,
                   [(LineReference('f)', parent), 4),
                    (LineReference('g)', parent), 8), (parent, 14)])

        parent = ArticleReference('26º')
        self._test('nas alíneas f) e g) do artigo 26º', managers,
                   [(LineReference('f)', parent), 4),
                    (LineReference('g)', parent), 8), (parent, 14)])

    def test_with_document(self):
        managers = [ObserverManager({'Decreto-Lei': DocumentsObserver}),
                    ObserverManager({'artigo': ArticlesObserver}),
                    ObserverManager({'nº': NumbersObserver}),
                    ObserverManager({'alíneas': LineObserver})]

        document = DocumentReference('2/2013', Token('Decreto-Lei'))
        article = ArticleReference('26º', document)
        number = NumberReference('4', article)

        self._test('nas alíneas f) e g) do nº 4 do artigo 26º '
                   'do Decreto-Lei nº 2/2013', managers,
                   [(LineReference('f)', number), 4),
                    (LineReference('g)', number), 8), (number, 14),
                    (article, 20), (document, 28)])


class TestAnchorArticle(GeneralTestCase):

    def test_simple(self):
        managers = parser.common_managers

        line = Article('1º')
        self._test('\nArtigo 1º\n', managers, [(line, 1)])


class TestAnchorNumber(GeneralTestCase):

    def test_simple(self):
        managers = parser.common_managers

        line = Number('1')
        self._test('\n1 - test\n', managers, [(line, 1)])


class TestAnchorLine(GeneralTestCase):

    def test_simple(self):
        managers = parser.common_managers

        line = Line('a)')
        self._test('\na) test\n', managers, [(line, 1)])
