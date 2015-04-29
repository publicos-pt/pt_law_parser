import os.path
import unittest

from pt_law_downloader import get_publication

from pt_law_parser.normalizer import normalize
from pt_law_parser.analyser import parse, analyse
from pt_law_parser.html import html_toc, valid_html
from pt_law_parser.json import from_json


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
        #    f.write(html)

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

        result = analyse(parse(normalized))

        # useful to store the result
        #with open('s.html', 'w') as f:
        #    f.write(html)

        self.assertEqual(_expected('%d.html' % publication['dre_id']),
                         valid_html(result.as_html()))
        self.assertEqual(normalized, result.as_str())
        self.assertEqual(result, from_json(result.as_json()))
        return result

    def test_simple(self):
        """
        Test failing due to DocumentObserver catching EU laws.
        """
        publication = get_publication(67040491)
        result = self._test(publication)

        # test recursive search for references
        self.assertEqual(23, len(list(result.get_doc_refs())))

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
