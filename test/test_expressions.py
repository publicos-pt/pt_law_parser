import unittest

from pt_law_parser.expressions import DocumentReference, Token


class TestDocument(unittest.TestCase):

    def test_href(self):
        doc = DocumentReference('2/2002', Token('Decreto'))

        doc.set_href('http://www.example.com')

        self.assertEqual('<a href="http://www.example.com">2/2002</a>',
                         doc.as_html())
