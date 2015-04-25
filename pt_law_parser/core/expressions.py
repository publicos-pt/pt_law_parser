class AbstractCompilable(object):
    """
    An abstract class that defines an API to transform itself into other types
    of expressions.
    """
    def as_str(self):
        raise NotImplementedError

    def __eq__(self, other):
        if isinstance(other, str):
            return self.as_str() == other
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, repr(self.as_str()))


class Expression(list, AbstractCompilable):
    """
    A general expression.
    """
    def as_str(self):
        return ''.join(v.as_str() for v in self)


class Token(AbstractCompilable):

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

    @parent.setter
    def parent(self, parent):
        self._parent = parent

    @property
    def number(self):
        return self._string

    @number.setter
    def number(self, token):
        assert isinstance(token, Token)
        self._string = token.as_str()


class DocumentReference(Reference):

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__,
                            repr(str(self)))

    def __str__(self):
        return self.parent.as_str() + ' ' + self.number


class LineReference(Reference):

    def __str__(self):
        return 'Alínea %s' % self.number


class NumberReference(Reference):

    def __str__(self):
        return 'nº %s' % self.number


class ArticleReference(Reference):

    def __str__(self):
        return 'Artigo %s' % self.number


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
