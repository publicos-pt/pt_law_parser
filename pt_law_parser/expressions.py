class AbstractCompilable(object):
    """
    An abstract class that defines an API to transform itself into other types
    of expressions.
    """
    def as_str(self):
        raise NotImplementedError

    def as_html(self):
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
    def as_html(self):
        return ''.join(v.as_html() for v in self)

    def as_str(self):
        return ''.join(v.as_str() for v in self)


class Token(AbstractCompilable):

    def __init__(self, string):
        assert isinstance(string, str)
        self._string = string

    def as_str(self):
        return self._string

    def as_html(self):
        return '<span class="%s">%s</span>' % (self.__class__.__name__,
                                               self.as_str())


class Separator(Token):
    def __init__(self, separator):
        assert len(separator) == 1
        super(Separator, self).__init__(separator)


class EndOfLine(Token):

    def __init__(self):
        super(EndOfLine, self).__init__('')

    def as_html(self):
        return ''

    def as_str(self):
        return ''


class Reference(Token):
    def __init__(self, type, number, parent=None):
        super(Reference, self).__init__(number)
        assert isinstance(type, str)
        assert isinstance(number, str)
        assert isinstance(parent, Reference) or parent is None
        self._type = type
        self._parent = parent

    def as_str(self):
        return '%s %s' % (self.type, self.number)

    def __repr__(self):
        parent = 'None'
        if self.parent:
            parent = self.parent.as_str()
        return '<%s %s %s>' % (self.__class__.__name__,
                                  repr(self.as_str()), repr(parent))

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        self._parent = parent

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, token):
        assert isinstance(token, Token)
        self._type = token.as_str()

    @property
    def number(self):
        return self._string

    @number.setter
    def number(self, token):
        assert isinstance(token, Token)
        self._string = token.as_str()


class LineReference(Reference):
    def __init__(self, number, parent=None):
        super(LineReference, self).__init__('Alínea', number, parent)


class NumberReference(Reference):
    def __init__(self, number, parent=None):
        super(NumberReference, self).__init__('nº', number, parent)


class ArticleReference(Reference):
    def __init__(self, number, parent=None):
        super(ArticleReference, self).__init__('Artigo', number, parent)
