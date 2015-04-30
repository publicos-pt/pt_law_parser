"""
Contains all elements of this package. They act as the formal elements of the law.
"""


class BaseElement(object):
    """
    Defines the interface of all elements.
    """
    def as_html(self):
        raise NotImplementedError

    def as_str(self):
        raise NotImplementedError

    def as_json(self):
        raise NotImplementedError

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, repr(self.as_str()))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.as_json() == other.as_json()
        else:
            return False

    @staticmethod
    def _build_html(tag, text, attrib):
        text = text.replace('\n', '')  # \n have no meaning in HTML
        if not text:
            # ignore empty elements
            return ''

        attributes = ' '.join('%s="%s"' % (key, value)
                              for (key, value) in sorted(attrib.items())
                              if value is not None)
        if attributes:
            attributes = ' ' + attributes

        return '<{0}{1}>{2}</{0}>'.format(tag, attributes, text)


class Token(BaseElement):

    def __init__(self, string):
        assert isinstance(string, str)
        self._string = string

    def as_str(self):
        return self.string

    def as_html(self):
        return self.as_str()

    def as_json(self):
        return {self.__class__.__name__: [self.as_str()]}

    @property
    def string(self):
        return self._string


class Reference(Token):
    def __init__(self, number, parent=None):
        super(Reference, self).__init__(number)
        assert isinstance(number, str)
        assert isinstance(parent, Token) or parent is None
        self._parent = parent

    def __repr__(self):
        return '<%s %s %s>' % (self.__class__.__name__,
                               repr(self.number), repr(self.parent))

    def as_html(self):
        return self._build_html('a', self.as_str(), {})

    def as_json(self):
        r = {self.__class__.__name__: [self.number]}
        if self.parent:
            r[self.__class__.__name__].append(self.parent.as_json())
        return r

    @property
    def number(self):
        return self.string

    @property
    def parent(self):
        return self._parent


class DocumentReference(Reference):

    def __init__(self, number, parent, href=''):
        super(DocumentReference, self).__init__(number, parent)
        self._href = href

    def __repr__(self):
        return '<%s %s %s>' % (self.__class__.__name__, repr(self.as_str()),
                               repr(self.parent.as_str()))

    @property
    def name(self):
        return self.parent.as_str()

    def set_href(self, href):
        self._href = href

    def as_html(self):
        if self._href:
            return self._build_html('a', self.as_str(), {'href': self._href})
        return super(DocumentReference, self).as_html()

    def as_json(self):
        r = super(DocumentReference, self).as_json()
        if self._href:
            r[self.__class__.__name__].append(self._href)
        return r


class LineReference(Reference):
    pass


class NumberReference(Reference):
    pass


class ArticleReference(Reference):
    pass


class EULawReference(Reference):

    @staticmethod
    def _build_eu_url(name, number):
        # example: '2000/29/CE'
        year, iden, _ = number.split('/')
        label = {'Diretiva': 'L',
                 'Decisão de Execução': 'D'}[name]
        # regulation missing, e.g. 31992R2081

        eur_id = '3%s%s%04d' % (year, label, int(iden))

        return 'http://eur-lex.europa.eu/legal-content/PT/TXT/?uri=CELEX:%s' \
               % eur_id

    def __init__(self, number, parent):
        super(EULawReference, self).__init__(number, parent)

    def as_html(self):
        return self._build_html('a', self.as_str(),
                                {'href': self._build_eu_url(self.parent.as_str(),
                                                            self.number)})


class Anchor(Token):
    name = None

    def __init__(self, string):
        super(Anchor, self).__init__(string)
        self._document_section = None

    def as_str(self):
        return '%s %s\n' % (self.name, self.number)

    def as_json(self):
        return {self.__class__.__name__: [self.number]}

    @property
    def number(self):
        return self.string

    @property
    def format(self):
        return self.__class__

    @property
    def reference(self):
        return self._document_section

    @reference.setter
    def reference(self, document_section):
        assert(isinstance(document_section, DocumentSection))
        self._document_section = document_section

    def ref_as_href(self):
        if self.reference.id_as_html():
            return '#' + self.reference.id_as_html()
        else:
            return None


class Section(Anchor):
    name = 'Secção'


class SubSection(Anchor):
    name = 'Sub-Secção'


class Part(Anchor):
    name = 'Parte'


class Chapter(Anchor):
    name = 'Capítulo'


class Title(Anchor):
    name = 'Título'


class Annex(Anchor):
    name = 'Anexo'

    def as_str(self):
        if self.number:
            return '%s %s\n' % (self.name, self.number)
        else:
            return '%s\n' % self.name


class Article(Anchor):
    name = 'Artigo'

    def as_html(self):
        anchor = self._build_html('a', self.number,
                                  {'href': self.ref_as_href()})
        return '%s %s' % (self.name, anchor)


class Number(Anchor):
    name = 'Número'

    def as_str(self):
        return '%s -' % self.number

    def as_html(self):
        return self._build_html('a', self.as_str(),
                                {'href': self.ref_as_href()})


class Line(Number):
    name = 'Alínea'

    def as_str(self):
        return '%s' % self.number


class BaseDocumentSection(BaseElement):

    def __init__(self, *children):
        self._children = []
        for child in children:
            self.append(child)
        self._parent_section = None

    def append(self, element):
        if isinstance(element, BaseDocumentSection):
            element._parent_section = self
        self._children.append(element)

    def __getitem__(self, item):
        return self._children[item]

    def __len__(self):
        return len(self._children)

    def as_str(self):
        return ''.join(child.as_str() for child in self._children)

    @staticmethod
    def _as_html(children):
        string = ''
        ol = False
        for child in children:
            if not ol and isinstance(child, InlineDocumentSection):
                string += '<ol>'
                ol = True
            string += child.as_html()
            # this never happens so far.
            #if ol and not isinstance(child, InlineDocumentSection):
            #    string += '</ol>'
            #    ol = False
        if ol:
            string += '</ol>'

        return string

    def as_html(self):
        return self._as_html(self._children)

    def as_json(self):
        return {self.__class__.__name__: [child.as_json() for child in
                                          self._children]}

    def find_all(self, condition, recursive=False):
        if recursive:
            def _find_all(root):
                result = []
                if isinstance(root, BaseDocumentSection):
                    for child in root._children:
                        if condition(child):
                            result.append(child)
                        result += _find_all(child)
                return result
            return _find_all(self)

        return [child for child in self._children if condition(child)]

    def id_tree(self):
        tree = []
        if self._parent_section is not None:
            tree = self._parent_section.id_tree()
        tree += [self]
        return tree

    def get_doc_refs(self):
        """
        Yields tuples (name, number) of all its `DocumentReference`s.
        """
        refs = self.find_all(lambda x: isinstance(x, DocumentReference), True)
        ref_set = set()
        for ref in refs:
            ref_set.add((ref.name, ref.number))
        return ref_set

    def set_doc_refs(self, mapping):
        """
        Uses a dictionary of the form `(name, ref)-> url` to set the href
        of its own `DocumentReference`s.
        """
        refs = self.find_all(lambda x: isinstance(x, DocumentReference), True)
        for ref in refs:
            if (ref.name, ref.number) in mapping:
                ref.set_href(mapping[(ref.name, ref.number)])


class Paragraph(BaseDocumentSection):

    def as_html(self):
        return self._build_html('p', super(Paragraph, self).as_html(), {})


class InlineParagraph(Paragraph):
    def as_html(self):
        return self._build_html('span', super(Paragraph, self).as_html(), {})


class Document(BaseDocumentSection):
    pass


class DocumentSection(BaseDocumentSection):
    formal_sections = [Annex, Article, Number, Line]

    html_classes = {
        Annex: 'annex',
        Part: 'part',
        Title: 'title',
        Chapter: 'chapter',
        Section: 'section',
        SubSection: 'sub-section',
        Article: 'article',
        Number: 'number list-unstyled',
        Line: 'line list-unstyled'}

    def __init__(self, *children):
        assert(isinstance(children[0], Anchor))
        super(DocumentSection, self).__init__(*children)
        self.anchor.reference = self

    @property
    def anchor(self):
        return self[0]

    @property
    def format(self):
        return self.anchor.format

    def formal_id_tree(self):
        filtered_tree = []
        for e in self.id_tree():
            if isinstance(e, QuotationSection):
                return []  # sections inside quotations have no tree
            if isinstance(e, DocumentSection) and e.format in self.formal_sections:
                filtered_tree.append(e)

        return filtered_tree

    def id_as_html(self):
        string = '-'.join(e.anchor.name + '-' + e.anchor.number for e in
                          self.formal_id_tree())
        if string != '':
            return string
        else:
            return None


class TitledDocumentSection(DocumentSection):

    hierarchy_html_titles = {
        Part: 'h2',
        Annex: 'h2',
        Title: 'h3',
        Chapter: 'h3',
        Section: 'h4',
        SubSection: 'h5',
        Article: 'h5'}

    def as_html(self):
        inner = self._as_html(self._children[:2])
        container = self._build_html(self.hierarchy_html_titles[self.format],
                                     inner, {'class': 'title'})
        rest = self._as_html(self._children[2:])

        return self._build_html('div', container + rest,
                                {'class': self.html_classes[self.format],
                                 'id': self.id_as_html()})

    @property
    def title(self):
        return self.anchor.as_str() + ' ' + self._children[1].as_str()


class InlineDocumentSection(DocumentSection):
    html_lists = {Number: 'li', Line: 'li'}

    def as_html(self):
        first = self._as_html(self._children[:1])
        container = self._build_html('span', first, {})
        rest = self._as_html(self._children[1:])
        return self._build_html('li', container + rest,
                                {'class': self.html_classes[self.format],
                                 'id': self.id_as_html()})


class QuotationSection(BaseDocumentSection):
    """
    A Section quoting something.
    """
    def as_html(self):
        return '<blockquote>%s</blockquote>' % \
               super(QuotationSection, self).as_html()

    def as_str(self):
        return '«%s»' % super(QuotationSection, self).as_str()
