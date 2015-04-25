from collections import OrderedDict

from pt_law_parser.core import expressions


class BaseElement(object):

    def __init__(self):
        self._children = []

    def append(self, element):
        self._children.append(element)
        element.set_parent(self)

    def remove(self, element):
        element.clean_parent()
        self._children.remove(element)

    def __getitem__(self, item):
        return self._children[item]

    def __len__(self):
        return len(self._children)

    def as_html(self):
        string = ''
        for child in self._children:
            string += child.as_html()
        return string

    @property
    def text(self):
        string = ''
        for child in self._children:
            string += child.text
        return string


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

    def clean_parent(self):
        self._parent = None

    def as_html(self):
        attributes = ''.join('%s="%s" ' % (key, value)
                             for (key, value) in self._attrib.items())

        return '<{0} {1}>{2}</{0}>'.format(self.tag, attributes,
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
        self._number = reference.string
        self._parent = reference.parent
        self.append(Text(self._number))


class Anchor(Element):

    def __init__(self, anchor):
        assert(isinstance(anchor, expressions.Anchor))
        super(Anchor, self).__init__('p')
        self.append(Text(anchor.name + ' '))
        number = Element('a')
        number.append(Text(anchor.number))
        self.append(number)
        self.anchor_element_index = 1

    def set_href(self, href):
        self[self.anchor_element_index].attrib['href'] = href


class SpanAnchor(Anchor):

    def __init__(self, anchor):
        assert(isinstance(anchor, expressions.Anchor))
        super(Anchor, self).__init__('span')
        number = Element('a')
        number.append(Text(anchor.number))
        self.append(number)
        self.append(Text(' - '))
        self.anchor_element_index = 0
