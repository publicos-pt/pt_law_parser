class Token(object):

    def __init__(self, string):
        assert isinstance(string, str)
        self._string = string

    @property
    def string(self):
        return self._string

    def as_str(self):
        return self.string

    def __str__(self):
        return self.as_str()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            raise NotImplementedError

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, repr(self.as_str()))


class Reference(Token):
    def __init__(self, number, parent=None):
        super(Reference, self).__init__(number)
        assert isinstance(number, str)
        assert isinstance(parent, Token) or parent is None
        self._parent = parent

    def __repr__(self):
        return '<%s %s %s>' % (self.__class__.__name__,
                               repr(str(self)), repr(str(self.parent)))

    @property
    def parent(self):
        return self._parent


class DocumentReference(Reference):

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__,
                            repr(str(self)))


class LineReference(Reference):
    pass


class NumberReference(Reference):
    pass


class ArticleReference(Reference):
    pass


class EULawReference(Reference):
    pass


class Anchor(Token):
    name = None

    def __init__(self, string):
        self._number = string
        super(Anchor, self).__init__('%s %s' % (self.name, self._number))

    def as_str(self):
        return '%s\n' % self.string

    @property
    def number(self):
        return self._number


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


class Article(Anchor):
    name = 'Artigo'


class Number(Anchor):
    name = 'Número'

    def as_str(self):
        return '%s -' % self._number


class Line(Anchor):
    name = 'Alínea'

    def as_str(self):
        return '%s' % self._number
