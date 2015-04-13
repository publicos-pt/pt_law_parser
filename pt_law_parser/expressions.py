class AbstractCompilable(object):
    """
    An abstract class that defines an API to transform itself into other types
    of expressions.
    """
    def as_str(self):
        raise NotImplementedError

    def as_html(self):
        raise NotImplementedError


class Expression(AbstractCompilable):
    """
    A general expression.
    """
    def __init__(self, value):
        self._value = value

    def as_html(self):
        return ''.join(v.as_html() for v in self._value)

    def as_str(self):
        return ''.join(v.as_str() for v in self._value)


class Token(AbstractCompilable):

    def __init__(self, value):
        self._value = value

    def as_html(self):
        return self._value

    def as_text(self):
        return self._value


class Separator(Token):
    pass
