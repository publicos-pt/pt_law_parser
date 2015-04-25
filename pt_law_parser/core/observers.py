import re

from .expressions import Token, DocumentReference, ArticleReference, \
    NumberReference, LineReference, \
    Article, Number, Line, Annex, Title, Chapter, Part, Section, SubSection


BASE_ARTICLE_NUMBER_REGEX = '[\dA-Z\-]+º(?:\-[A-Z]+)?'
BASE_NUMBER_REGEX = '\d'
BASE_LINE_REGEX = '[\da-z]*\)'

DOCUMENT_NUMBER_REGEX = '^[\d\-A-Z]+/\d+(?:/[A-Z]*)?$'
ARTICLE_NUMBER_REGEX = '^%s$|^anterior$|^seguinte$' % BASE_ARTICLE_NUMBER_REGEX
NUMBER_REGEX = '^%s$|^anterior$|^seguinte$' % BASE_NUMBER_REGEX
LINE_REGEX = '^%s$' % BASE_LINE_REGEX


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

    def finish(self):
        self._is_done = True


class DocumentRefObserver(Observer):

    def __init__(self, index, token):
        super(DocumentRefObserver, self).__init__(index, token)

        self._numbers = {}

    def observe(self, index, token, caught):
        if not caught and re.match(DOCUMENT_NUMBER_REGEX, token.as_str()):
            self._numbers[index] = token
            return True

        if token in (Token('.'), Token('\n')):
            self._is_done = True

        return False

    def replace_in(self, result):
        type_token = Token(self._string)

        for i in self._numbers:
            result[i] = DocumentReference(self._numbers[i].as_str(), type_token)


class ArticleRefObserver(Observer):
    klass = ArticleReference

    def __init__(self, index, token):
        super(ArticleRefObserver, self).__init__(index, token)
        self._numbers = {}
        self._parent = None

    def observe(self, index, token, caught):
        if token in (Token('.'), Token('\n')):
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


class NumberRefObserver(ArticleRefObserver):
    klass = NumberReference

    def observe(self, index, token, caught):
        if token in (Token('.'), Token('\n')):
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


class LineRefObserver(ArticleRefObserver):
    klass = LineReference

    def observe(self, index, token, caught):
        if token in (Token('.'), Token('\n')):
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


class AnchorObserver(Observer):
    anchor_klass = None
    rules = []
    number_at = None
    take_up_to = None

    def __init__(self, index, token):
        super(AnchorObserver, self).__init__(index, token)
        self._number = None
        self._number_index = None

        self._is_valid = [False for _ in range(len(self.rules))]

    def observe(self, index, token, caught):

        if not self._is_valid[0]:
            if token.as_str() == '\n':
                self._is_valid[0] = True
            return

        for rule in range(1, len(self.rules)):
            if self._is_valid[rule]:
                continue
            if self._is_valid[rule - 1] and self.rules[rule](token.as_str()):
                # if last rule, is done
                if rule == len(self.rules):
                    self._is_done = True
                    return
                self._is_valid[rule] = True
                if rule == self.number_at:
                    self._number = token.as_str()
                    self._number_index = index
                break
            else:
                self._number = None
                self._number_index = None
                self._is_done = True
                break

    def replace_in(self, result):
        if self._number is not None:
            assert(self._number_index == self._index + self.number_at)
            for i in reversed(range(2, self.take_up_to)):
                result[self._index + i] = Token('')  # '\n'
            result[self._index + 1] = self.anchor_klass(self._number)


def common_rules(name, regex):
    return [lambda x: x == '\n', lambda x: x == name,
            lambda x: x == ' ', lambda x: re.match(regex, x),
            lambda x: x == '\n']


class ArticleObserver(AnchorObserver):
    anchor_klass = Article
    rules = common_rules(Article.name, BASE_ARTICLE_NUMBER_REGEX)
    number_at = 3
    take_up_to = 5


class SubSectionObserver(ArticleObserver):
    anchor_klass = SubSection
    rules = common_rules(SubSection.name, '[IVX]*')


class SectionObserver(ArticleObserver):
    anchor_klass = Section
    rules = common_rules(Section.name, '[IVX]*')


class PartObserver(ArticleObserver):
    anchor_klass = Part
    rules = common_rules(anchor_klass.name, '[IVX]*')


class ChapterObserver(ArticleObserver):
    anchor_klass = Chapter
    rules = common_rules(Chapter.name, '[IVX]*')


class AnnexObserver(ArticleObserver):
    anchor_klass = Annex
    rules = common_rules(Annex.name, '[IVX]*')


class TitleObserver(ArticleObserver):
    anchor_klass = Title
    rules = common_rules(Title.name, '[IVX]*')


class NumberObserver(AnchorObserver):
    anchor_klass = Number
    rules = [lambda x: x == '\n', lambda x: re.match(BASE_NUMBER_REGEX, x),
             lambda x: x == ' ', lambda x: x == '-', lambda x: x == ' ']
    number_at = 1
    take_up_to = 4


class LineObserver(AnchorObserver):
    anchor_klass = Line
    rules = [lambda x: x == '\n', lambda x: re.match(BASE_LINE_REGEX, x),
             lambda x: x == ' ']
    number_at = 1
    take_up_to = 2
