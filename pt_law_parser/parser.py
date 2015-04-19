import re

from .tokenizer import tokenize
from .expressions import Separator, Token, EndOfLine, Expression, \
    DocumentReference, ArticleReference, NumberReference, LineReference


DOCUMENT_NUMBER_REGEX = '^[\d\-A-Z]+/\d+(?:/[A-Z]*)?$'
ARTICLE_NUMBER_REGEX = '^[\dA-Z\-]+º(?:\-[A-Z]+)?$|^anterior$|^seguinte$'
NUMBER_REGEX = '^\d$|^anterior$|^seguinte$'
LINE_REGEX = '^[\da-z]*\)$'


class Observer(object):
    """
    A Token that is able to gather information to change its own state.

    It contains an `index` that identifies its position in the list it belongs.
    Uses `replace_in` to replace itself by its own `_real_class`, thus
    terminating its observation and itself.
    """
    def __init__(self, index, token):
        self._string = token.as_str()
        self._is_done = False
        self._index = index

    @property
    def is_done(self):
        return self._is_done

    def observe(self, index, token, caught):
        raise NotImplementedError

    def replace_in(self, result):
        raise NotImplementedError


class DocumentsObserver(Observer):

    def __init__(self, index, token):
        super(DocumentsObserver, self).__init__(index, token)

        self._numbers = {}

    def observe(self, index, token, caught):
        if not caught and re.match(DOCUMENT_NUMBER_REGEX, token.as_str()):
            self._numbers[index] = token
            return True

        if token in (Separator('.'), EndOfLine()):
            self._is_done = True

        return False

    def replace_in(self, result):
        type_token = Token(self._string)

        for i in self._numbers:
            result[i] = DocumentReference(self._numbers[i].as_str(), type_token)


class ArticlesObserver(Observer):
    klass = ArticleReference

    def __init__(self, index, token):
        super(ArticlesObserver, self).__init__(index, token)
        self._numbers = {}
        self._parent = None

    def observe(self, index, token, caught):
        if token in (Separator('.'), EndOfLine()):
            self._is_done = True

        if self._parent:
            return False

        if not caught and re.match(ARTICLE_NUMBER_REGEX, token.as_str()):
            self._numbers[index] = token
            return True
        elif re.match(DOCUMENT_NUMBER_REGEX, token.as_str()):
            self._parent = index

        return False

    def replace_in(self, result):
        parent = None
        if self._parent:
            parent = result[self._parent]
        for i in self._numbers:
            result[i] = self.klass(self._numbers[i].as_str(), parent)


class NumbersObserver(ArticlesObserver):
    klass = NumberReference

    def observe(self, index, token, caught):
        if token in (Separator('.'), EndOfLine()):
            self._is_done = True

        if self._parent:
            return False

        if not caught and re.match(NUMBER_REGEX, token.as_str()):
            self._numbers[index] = token
            return True
        elif re.match(ARTICLE_NUMBER_REGEX, token.as_str()):
            self._parent = index
        elif re.match(DOCUMENT_NUMBER_REGEX, token.as_str()):
            self._parent = index

        return False


class LineObserver(ArticlesObserver):
    klass = LineReference

    def observe(self, index, token, caught):
        if token in (Separator('.'), EndOfLine()):
            self._is_done = True

        if self._parent:
            return False

        if not caught and re.match(LINE_REGEX, token.as_str()):
            self._numbers[index] = token
            return True
        elif re.match(NUMBER_REGEX, token.as_str()):
            self._parent = index
        elif re.match(ARTICLE_NUMBER_REGEX, token.as_str()):
            self._parent = index
        elif re.match(DOCUMENT_NUMBER_REGEX, token.as_str()):
            self._parent = index

        return False


class ObserverManager(object):
    def __init__(self, rules):
        self._rules = rules
        self._observers = {}

    def generate(self, index, token):
        if token.as_str() in self._rules:
            observer = self._rules[token.as_str()](index, token)
            self._observers[index] = observer

    @property
    def terms(self):
        return set(self._rules.keys())

    def _items(self):
        return sorted(dict(self._observers).items(), reverse=True)

    def observe(self, index, token, caught):
        for i, observer in self._items():
            caught = observer.observe(index, token, caught) or caught
        return caught

    def replace_in(self, result):
        for i, observer in self._items():
            if observer.is_done:
                observer.replace_in(result)
                del self._observers[i]


def parse(string, managers, terms=set()):
    result = Expression()

    for manager in managers:
        terms |= manager.terms

    for index, token in enumerate(tokenize(string, ' ,.', terms)):
        result.append(token)

        caught = False
        for manager in managers:
            manager.generate(index, token)
            caught = manager.observe(index, token, caught) or caught
            manager.replace_in(result)

    return result
