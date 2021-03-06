import os.path
import unittest

from pt_law_downloader import get_publication

from pt_law_parser.normalizer import normalize
from pt_law_parser.analyser import analyse
from pt_law_parser.html import html_toc, valid_html
from pt_law_parser.expressions import from_json
from pt_law_parser import parser
from pt_law_parser.observers import DocumentRefObserver, ArticleRefObserver


def parse(text):
    type_names = ['Decreto-Lei', 'Lei', 'Declaração de Rectificação', 'Portaria']

    managers = parser.common_managers + [
        parser.ObserverManager(dict((name, DocumentRefObserver)
                                    for name in type_names)),
        parser.ObserverManager(dict((name, ArticleRefObserver)
                                    for name in ['artigo', 'artigos']))]

    terms = {' ', '.', ',', '\n', 'n.os', '«', '»'}
    for manager in managers:
        terms |= manager.terms

    return parser.parse(text, managers, terms)


def _expected(file):
    file_dir = os.path.dirname(__file__)
    with open(file_dir + '/expected/%s' % file) as f:
        expected_html = f.read()
    return expected_html


class TestCase(unittest.TestCase):

    def _test_json(self, input_file):
        file_dir = os.path.dirname(__file__)
        with open(file_dir + '/raw/%s' % input_file) as f:
            text = f.read()

        result = analyse(parse(text))

        self.assertEqual(result, from_json(result.as_json()))

    def _compare_texts(self, input_file, expected_file):
        file_dir = os.path.dirname(__file__)

        with open(file_dir + '/raw/%s' % input_file) as f:
            normalized = f.read()

        result = analyse(parse(normalized))

        # useful to store the result
        #with open('s.html', 'w') as f:
        #    f.write(valid_html(result.as_html()))

        self.assertEqual(_expected(expected_file),
                         valid_html(result.as_html()))
        self.assertEqual(normalized, result.as_str())
        self.assertEqual(result, from_json(result.as_json()))
        return result

    def _test(self, publication):
        file_dir = os.path.dirname(__file__) + '/expected/'

        normalized = normalize(publication['text'])

        # test normalization if it exists
        try:
            with open(file_dir + '%d_norm.html' % publication['dre_id']) as f:
                expected_norm = f.read()
            self.assertEqual(expected_norm, normalized)
        except IOError:
            pass

        #with open('s.txt', 'w') as f:
        #    f.write(normalized)

        result = analyse(parse(normalized))

        # useful to store the result
        #with open('s.html', 'w') as f:
        #    f.write(valid_html(result.as_html()))

        self.assertEqual(_expected('%d.html' % publication['dre_id']),
                         valid_html(result.as_html()))
        self.assertEqual(normalized, result.as_str())
        self.assertEqual(result, from_json(result.as_json()))
        return result

    def test_annex(self):
        """
        Tests document with an annex without number.
        """
        publication = get_publication(455149)
        self._test(publication)

    def test_simple(self):
        """
        Test failing due to DocumentObserver catching EU laws.
        """
        publication = get_publication(67040491)
        result = self._test(publication)

        # test recursive search for references: 15 unique references
        self.assertEqual(15, len(result.get_doc_refs()))

    def test_no_title(self):
        self._compare_texts('no_title.txt', 'no_title.html')

    def test_clause(self):
        self._compare_texts('clause.txt', 'clause.html')

    def test_basic(self):
        result = self._compare_texts('basic.txt', 'basic.html')

        mapping = {('Decreto-Lei', '2/2002'): 'http://example.com'}
        result.set_doc_refs(mapping)

        self.assertEqual(_expected('basic_w_refs.html'),
                         valid_html(result.as_html()))
        # assert that json stores urls of doc refs
        self.assertEqual(result, from_json(result.as_json()))

    def test_json(self):
        self._test_json('basic.txt')

    def test_69982738(self):
        """
        This document caused an error because it contained a reserved token
        for an itemization.
        """
        publication = get_publication(69982738)
        self._test(publication)


class TestToc(unittest.TestCase):

    def _test(self, publication_id):
        publication = get_publication(publication_id)
        result = analyse(parse(normalize(publication['text'])))
        toc = html_toc(result)

        toc = valid_html(toc.as_html())
        toc = toc.replace('<li', '\n<li').replace('<ul', '\n<ul')

        # useful to store the result
        #with open('toc.html', 'w') as f:
        #    f.write(toc)

        self.assertEqual(_expected('%d_toc.html' % publication_id), toc)

    def test_640339(self):
        self._test(640339)

    def test_67040491(self):
        self._test(67040491)
