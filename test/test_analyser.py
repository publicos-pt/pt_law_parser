import os.path
import unittest

from pt_law_downloader import get_publication

from pt_law_parser.normalizer import normalize
from pt_law_parser.analyser import parse, analyse


class TestCase(unittest.TestCase):

    def _compare_texts(self, input_file, expected_file):
        file_dir = os.path.dirname(__file__)

        with open(file_dir + '/raw/%s' % input_file) as f:
            text = f.read()

        result = analyse(parse(text))

        html = '<html xmlns="http://www.w3.org/1999/xhtml">'\
               '<head><meta http-equiv="Content-Type" content="text/html; ' \
               'charset=utf-8"></head>' + result.as_html() + '</html>'
        html = html.replace('<div', '\n<div').replace('<p', '\n<p').replace('<span', '\n<span')

        # useful to store the result
        #with open('s.html', 'w') as f:
        #    f.write(html)

        with open(file_dir + '/expected/%s' % expected_file) as f:
            expected_html = f.read()

        self.assertEqual(expected_html, html)
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
        html = html.replace('<div', '\n<div').replace('<p', '\n<p').replace('<span', '\n<span')

        with open(file_dir + '%d.html' % publication['dre_id']) as f:
            expected_html = f.read()

        self.assertEqual(expected_html, html)
        return result

    def test_basic(self):
        publication = get_publication(67040491)
        result = self._test(publication)

    def test_simple(self):
        self._compare_texts('basic.txt', 'basic.html')
