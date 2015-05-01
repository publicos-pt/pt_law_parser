import unittest

from pt_law_parser.expressions import DocumentReference, Token, Anchor, Annex


class TestDocument(unittest.TestCase):

    def test_href(self):
        doc = DocumentReference('2/2002', Token('Decreto'))

        doc.set_href('http://www.example.com')

        self.assertEqual('<a href="http://www.example.com">2/2002</a>',
                         doc.as_html())

    def test_not_equal(self):
        self.assertNotEqual(Token('bla'), Anchor('bla'))

    def test_annex(self):
        self.assertEqual('Anexo I\n', Annex('I').as_str())
        self.assertEqual('Anexo\n', Annex('').as_str())
