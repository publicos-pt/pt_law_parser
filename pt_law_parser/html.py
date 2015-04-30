from pt_law_parser.expressions import Document, TitledDocumentSection


class BaseElement(object):

    def __init__(self):
        self._children = []

    def append(self, element):
        assert(isinstance(element, (str, Element)))
        self._children.append(element)

    def as_html(self):
        string = ''
        for child in self._children:
            if isinstance(child, str):
                string += child
            else:
                string += child.as_html()
        return string


class Element(BaseElement):

    def __init__(self, tag, attrib=None):
        super(Element, self).__init__()
        self.tag = tag
        self._parent = None

        if attrib is None:
            self._attrib = {}
        else:
            self._attrib = attrib

    def as_html(self):
        attributes = ' '.join('%s="%s"' % (key, value)
                              for (key, value) in sorted(self._attrib.items()))
        if attributes:
            attributes = ' ' + attributes

        return '<{0}{1}>{2}</{0}>'.format(self.tag, attributes,
                                          super(Element, self).as_html())


def html_toc(document):
    assert(isinstance(document, Document))

    index = Element('div')

    def _add_to_index(element, root):
        titles = element.find_all(lambda x: isinstance(x, TitledDocumentSection))

        if titles:
            ul_tag = Element('ul', {'class': 'tree'})
        else:
            return None

        for child in titles:
            name = child.title
            anchor = child.anchor

            if anchor.ref_as_href():
                tag = Element('a', {'href': anchor.ref_as_href()})
            else:
                tag = Element('h5', {'class': 'tree-toggler'})
            tag.append(name)

            li_tag = Element('li')
            li_tag.append(tag)
            _add_to_index(child, li_tag)
            ul_tag.append(li_tag)

        root.append(ul_tag)

    _add_to_index(document, index)
    return index


def valid_html(html):
        html = '<html xmlns="http://www.w3.org/1999/xhtml">'\
               '<head><meta http-equiv="Content-Type" content="text/html; ' \
               'charset=utf-8"></head>' + html + '</html>'
        html = html.replace('\n', '').replace('<div', '\n<div')\
            .replace('<p', '\n<p').replace('<span', '\n<span')
        return html
