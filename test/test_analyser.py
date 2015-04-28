import os.path
import unittest

from pt_law_downloader import get_publication

from pt_law_parser.normalizer import normalize
from pt_law_parser.analyser import parse, analyse
from pt_law_parser.html import html_toc
from pt_law_parser.json import decode
from pt_law_parser.core.expressions import DocumentReference


class TestCase(unittest.TestCase):

    def _test_json(self, input_file):
        file_dir = os.path.dirname(__file__)
        with open(file_dir + '/raw/%s' % input_file) as f:
            text = f.read()

        result = analyse(parse(text))

        self.assertEqual(result, decode(result.as_json()))

    def _compare_texts(self, input_file, expected_file):
        file_dir = os.path.dirname(__file__)

        with open(file_dir + '/raw/%s' % input_file) as f:
            normalized = f.read()

        result = analyse(parse(normalized))

        html = '<html xmlns="http://www.w3.org/1999/xhtml">'\
               '<head><meta http-equiv="Content-Type" content="text/html; ' \
               'charset=utf-8"></head>' + result.as_html() + '</html>'
        html = html.replace('\n', '').replace('<div', '\n<div')\
            .replace('<p', '\n<p').replace('<span', '\n<span')

        # useful to store the result
        #with open('s.html', 'w') as f:
        #    f.write(html)

        with open(file_dir + '/expected/%s' % expected_file) as f:
            expected_html = f.read()

        self.assertEqual(expected_html, html)
        self.assertEqual(normalized, result.as_str())
        self.assertEqual(result, decode(result.as_json()))
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

        html = '<html xmlns="http://www.w3.org/1999/xhtml">'\
               '<head><meta http-equiv="Content-Type" content="text/html; ' \
               'charset=utf-8"></head>' + result.as_html() + '</html>'

        # pretty print to facilitate visualization
        html = html.replace('\n','').replace('<div', '\n<div').replace('<p', '\n<p').replace('<span', '\n<span')

        # useful to store the result
        #with open('s.html', 'w') as f:
        #    f.write(html)

        with open(file_dir + '%d.html' % publication['dre_id']) as f:
            expected_html = f.read()

        self.assertEqual(expected_html, html)
        self.assertEqual(normalized, result.as_str())
        self.assertEqual(result, decode(result.as_json()))
        return result

    def test_basic(self):
        """
        Test failing due to DocumentObserver catching EU laws.
        """
        publication = get_publication(67040491)
        result = self._test(publication)

        # test recursive search for references
        self.assertEqual(23, len(
            result.find_all(lambda x: isinstance(x, DocumentReference), True)))

    def test_simple(self):
        self._compare_texts('basic.txt', 'basic.html')

    def test_json(self):
        self._test_json('basic.txt')


class TestToc(unittest.TestCase):

    def _test(self, publication_id):
        publication = get_publication(publication_id)
        result = analyse(parse(normalize(publication['text'])))
        toc = html_toc(result)

        toc = '<html xmlns="http://www.w3.org/1999/xhtml">'\
                   '<head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"></head>'\
                   + toc.as_html() + '</html>'
        toc = toc.replace('\n', '').replace('<li', '\n<li').replace('<ul', '\n<ul')

        # useful to store the result
        #with open('s.html', 'w') as f:
        #    f.write(toc)

        file_dir = os.path.dirname(__file__)
        with open(file_dir + '/expected/%d_toc.html' % publication_id) as f:
            expected_html = f.read()

        self.assertEqual(expected_html, toc)

    def test_640339(self):
        self._test(640339)

    def test_67040491(self):
        self._test(67040491)
