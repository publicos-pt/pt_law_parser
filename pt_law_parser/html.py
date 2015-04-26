from collections import OrderedDict

from pt_law_parser.core import expressions


class BaseElement(object):

    def __init__(self):
        self._children = []

    def append(self, element):
        self._children.append(element)
        element.set_parent(self)

    def __getitem__(self, item):
        return self._children[item]

    def __len__(self):
        return len(self._children)

    def as_html(self):
        string = ''
        for child in self._children:
            string += child.as_html()
        return string

    def find_all(self, condition):
        return [child for child in self._children if condition(child)]

    @property
    def text(self):
        return ''.join(child.text for child in self._children)


class Document(BaseElement):

    def __init__(self):
        super(Document, self).__init__()


class Element(BaseElement):

    def __init__(self, tag, attrib=None):
        super(Element, self).__init__()
        self.tag = tag
        self._parent = None

        if attrib is None:
            self._attrib = OrderedDict()
        else:
            self._attrib = OrderedDict(attrib)

    @property
    def attrib(self):
        return self._attrib

    def set_parent(self, parent):
        self._parent = parent

    def as_html(self):
        attributes = ' '.join('%s="%s"' % (key, value)
                              for (key, value) in self._attrib.items())
        if attributes:
            attributes = ' ' + attributes

        return '<{0}{1}>{2}</{0}>'.format(self.tag, attributes,
                                          super(Element, self).as_html())

    def set_id(self, id):
        self.attrib['id'] = id


class Text(Element):

    def __init__(self, text=''):
        assert(isinstance(text, str))
        super(Text, self).__init__('')
        self._text = text

    def __iadd__(self, other):
        assert(isinstance(other, str))
        self._text += other

    def as_html(self):
        return self._text

    @property
    def text(self):
        return self._text


class Reference(Element):

    def __init__(self, reference):
        assert(isinstance(reference, expressions.Reference))
        super(Reference, self).__init__('a', {'href': '#'})
        self._reference = reference
        self.append(Text(reference.string))


def build_eu_url(name, number):
    # example: '2000/29/CE'
    year, id, _ = number.split('/')
    label = {'Diretiva': 'L',
             'Decisão de Execução': 'D'}[name]
    # regulation missing, e.g. 31992R2081

    eur_id = '3%s%s%04d' % (year, label, int(id))

    return 'http://eur-lex.europa.eu/legal-content/PT/TXT/?uri=CELEX:%s' % eur_id


class EULawReference(Reference):

    def __init__(self, reference):
        assert(isinstance(reference, expressions.EULawReference))
        super(EULawReference, self).__init__(reference)
        self.attrib['href'] = build_eu_url(reference.parent.as_str(), reference.string)


class Anchor(Element):
    """
    An anchor to some expressions.Anchor. It contains information about what
    the anchor is pointing to, and knows how to transform itself to html.
    """
    def __init__(self, anchor, tag):
        assert(isinstance(anchor, expressions.Anchor))
        super(Anchor, self).__init__(tag)
        self._anchor = anchor
        self.anchor_element_index = None

    @property
    def href(self):
        return self[self.anchor_element_index].attrib.get('href', None)

    @href.setter
    def href(self, href):
        self[self.anchor_element_index].attrib['href'] = href

    @property
    def number(self):
        return self._anchor.number

    @property
    def format(self):
        return self._anchor.__class__


class ArticleTitle(Anchor):
    def __init__(self, anchor):
        super(ArticleTitle, self).__init__(anchor, 'a')
        self.append(Text(anchor.name + ' '))
        number = Element('a')
        number.append(Text(anchor.number))
        self.append(number)
        self.anchor_element_index = 1


class NumberTitle(Anchor):

    def __init__(self, anchor):
        assert(isinstance(anchor, expressions.Number))
        super(NumberTitle, self).__init__(anchor, 'span')
        number = Element('a')
        number.append(Text(anchor.as_str()))
        self.append(number)
        self.append(Text(' '))
        self.anchor_element_index = 0


class LineTitle(Anchor):

    def __init__(self, anchor):
        assert(isinstance(anchor, expressions.Line))
        super(LineTitle, self).__init__(anchor, 'span')
        number = Element('a')
        number.append(Text(anchor.as_str()))
        self.append(number)
        self.append(Text(' '))
        self.anchor_element_index = 0


class AnnexTitle(ArticleTitle):
    pass


class SectionTitle(ArticleTitle):
    pass


class Section(Element):
    html_lists = {expressions.Number: 'li', expressions.Line: 'li'}
    html_classes = {
        expressions.Annex: 'annex',
        expressions.Part: 'part',
        expressions.Title: 'title',
        expressions.Chapter: 'chapter',
        expressions.Section: 'section',
        expressions.SubSection: 'sub-section',
        expressions.Article: 'article',
        expressions.Number: 'number list-unstyled',
        expressions.Line: 'line list-unstyled'}

    def _params(self, anchor):
        tag = 'div'
        if anchor.format in self.html_lists:
            tag = self.html_lists[anchor.format]

        return tag, {'class': self.html_classes[anchor.format]}

    def __init__(self, anchor):
        assert(isinstance(anchor, Anchor))
        super(Section, self).__init__(*self._params(anchor))
        self.append(anchor)


class TitledSection(Section):

    def __init__(self, anchor):
        from pt_law_parser import constants
        super(Section, self).__init__(*self._params(anchor))

        # create title container
        container = Element(constants.hierarchy_html_titles[anchor.format],
                            attrib={'class': 'title'})
        container.append(anchor)

        self.append(container)

    @property
    def title(self):
        return ' '.join(c.text for c in self[0]._children)

    @property
    def anchor(self):
        return self[0][0]
