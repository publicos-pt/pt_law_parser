"""
This module contains Observers: entities used in the parser to interpret sequences
of tokens into elements.
"""

import re

from pt_law_parser.expressions import Token, DocumentReference, ArticleReference, \
    NumberReference, LineReference, EULawReference, Clause, \
    Article, Number, Line, Annex, Title, Chapter, Part, Section, SubSection, Anchor, \
    Reference


BASE_ARTICLE_NUMBER_REGEX = '[\dA-Z\-]+º(?:\-[A-Z]+)?'
BASE_NUMBER_REGEX = '\d'
BASE_LINE_REGEX = '[\da-z]*\)'

DOCUMENT_NUMBER_REGEX = '^[\d\-A-Z]+/(?:\d{4}|\d{2})(?:/[A-Z]{1})?$'
ARTICLE_NUMBER_REGEX = '^%s$|^anterior$|^seguinte$' % BASE_ARTICLE_NUMBER_REGEX
NUMBER_REGEX = '^%s$|^anterior$|^seguinte$' % BASE_NUMBER_REGEX
LINE_REGEX = '^%s$' % BASE_LINE_REGEX
EULAW_NUMBER_REGEX = '^\d{4}/\d+(?:/CE|/UE)?$'


class Observer(object):
    """
    A generic object that observes a list of tokens and change its own state
    accordingly. Works like a state machine where the list of tokens is the tape.

    Initialize it with the `index` that identifies its position in the list of
    tokens and respective `token`.

    Use `observe` with a new index and new token. Its final state is a tuple of
    booleans (`is_done`, `needs_replace`):

    * `is_done` indicates that its observation is completed and thus it is ready
      to be deleted;
    * `needs_replace` indicates whether it requires replacing itself in the list
      of tokens using `replace_in` or not.

    Use `finish` to finalise its activity (i.e. sets `is_done=True`)
    """
    def __init__(self, index, token):
        self._string = token.as_str()
        self._is_done = False
        self._needs_replace = False
        self._index = index

    @property
    def is_done(self):
        return self._is_done

    @property
    def needs_replace(self):
        return self._needs_replace

    def _failed(self):
        self._is_done = True
        self._needs_replace = False

    def observe(self, index, token, caught):
        raise NotImplementedError

    def _replace_in(self, result):
        raise NotImplementedError

    def replace_in(self, result):
        assert self._needs_replace
        self._replace_in(result)

    def finish(self):
        if not self._is_done:
            self._failed()


class RefObserver(Observer):
    """
    A generic Observer for references.
    """
    klass = Reference

    def __init__(self, index, token):
        super(RefObserver, self).__init__(index, token)
        self._numbers = {}
        self._parent = None

    def _replace_in(self, result):
        parent = None
        if self._parent is not None:
            parent = result[self._parent]
        for i in self._numbers:
            result[i] = self.klass(self._numbers[i].as_str(), parent)

    def finish(self):
        self._is_done = True
        if self._numbers:
            self._needs_replace = True
        else:
            self._failed()


class DocumentRefObserver(RefObserver):
    klass = DocumentReference

    def __init__(self, index, token):
        super(DocumentRefObserver, self).__init__(index, token)
        self._parent = index

    def observe(self, index, token, caught):
        if not caught and re.match(DOCUMENT_NUMBER_REGEX, token.as_str()):
            self._numbers[index] = token
            return True

        if token in (Token('.'), Token('\n')):
            self.finish()

        return False


class ArticleRefObserver(RefObserver):
    klass = ArticleReference

    def __init__(self, index, token):
        super(ArticleRefObserver, self).__init__(index, token)
        self._parent = None

    def observe(self, index, token, caught):
        if token in (Token('.'), Token('\n')):
            self.finish()
            return False

        if self._parent:
            return False

        if not caught and re.match(ARTICLE_NUMBER_REGEX, token.as_str()):
            self._numbers[index] = token
            return True
        elif re.match(DOCUMENT_NUMBER_REGEX, token.as_str()):
            self._parent = index

        return False


class NumberRefObserver(ArticleRefObserver):
    klass = NumberReference

    def observe(self, index, token, caught):
        if token in (Token('.'), Token('\n')):
            self.finish()
            return False

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
            self.finish()
            return False

        if self._parent:
            return False

        if not caught and re.match(LINE_REGEX, token.as_str()):
            self._numbers[index] = token
            return True
        elif re.match(NUMBER_REGEX, token.as_str()):
            self._parent = index
        elif re.match(ARTICLE_NUMBER_REGEX, token.as_str()):
            self._parent = index
        # never found such case
        # elif re.match(DOCUMENT_NUMBER_REGEX, token.as_str()):
        #    self._parent = index

        return False


class GenericRuleObserver(Observer):
    """
    A generic observer that uses a strict match of a sequence of tokens to
    find matches. It is similar to a regex sub.

    The class attribute `_rules` is a list of functions that accept one string
    argument and return a bool. The observer `needs_replace` when all its rules
    were valid. The first rule must return True when for the token the observer
    is initialized.
    """
    _rules = []

    def __init__(self, index, token):
        super(GenericRuleObserver, self).__init__(index, token)

        self._is_valid = [False for _ in range(len(self._rules))]

    def _gather(self, index, token, rule):
        """
        This function is called on every `observe` and can be overwritten to
        store relevant tokens. `index` and `token` are the parameters of the
        observe, `rule` is the index of current rule. By default does nothing.
        """
        pass

    def observe(self, index, token, caught):
        if not self._is_valid[0]:
            assert(self._rules[0](token.as_str()))
            self._is_valid[0] = True
            return

        for rule in range(1, len(self._rules)):
            if self._is_valid[rule]:
                continue
            if self._is_valid[rule - 1] and self._rules[rule](token.as_str()):
                # if last rule, it is done
                self._is_valid[rule] = True
                self._gather(index, token, rule)
                if rule == len(self._rules) - 1:
                    self._is_done = True
                    self._needs_replace = True
                    return
                break
            else:
                self._failed()
                break


class EULawRefObserver(GenericRuleObserver):
    """
    A concrete observer for EU laws.
    """
    _rules = [lambda x: x in ('Diretiva', 'Decisão de Execução',
                              'Regulamento (CE)'),
              lambda x: x == ' ', lambda x: x == 'nº', lambda x: x == ' ',
              lambda x: re.match(EULAW_NUMBER_REGEX, x)]

    def __init__(self, index, token):
        super(EULawRefObserver, self).__init__(index, token)
        self._index = None
        self._number = None

    def _gather(self, index, token, rule):
        if rule == 4:
            self._index = index
            self._number = token.as_str()

    def _replace_in(self, result):
        result[self._index] = EULawReference(self._number, Token(self._string))


class AnchorObserver(GenericRuleObserver):
    """
    A generic observer for anchors. `anchor_klass` is the class this observer
    replaces `Token` by, `number_at` is the `rule` of the number of the anchor,
    if any, and `take_up_to` is the index up to which Tokens are removed from
    `result`. See subclasses for concrete examples.
    """
    anchor_klass = Anchor
    number_at = None
    take_up_to = 0

    def __init__(self, index, token):
        super(AnchorObserver, self).__init__(index, token)
        self._number = None
        self._number_index = None

    def _gather(self, index, token, rule):
        if rule == self.number_at:
            self._number = token.as_str()
            self._number_index = index

    def replace_in(self, result):
        assert(self._number_index == self._index + self.number_at)
        for i in reversed(range(2, self.take_up_to + 1)):
            result[self._index + i] = Token('')  # '\n'
        result[self._index + 1] = self.anchor_klass(self._number)


def common_rules(name, regex):
    return [lambda x: x == '\n', lambda x: x == name,
            lambda x: x == ' ', lambda x: re.match(regex, x),
            lambda x: x == '\n']


class ArticleObserver(AnchorObserver):
    anchor_klass = Article
    _rules = common_rules(Article.name, BASE_ARTICLE_NUMBER_REGEX + '|único')
    number_at = 3
    take_up_to = 4


class SubSectionObserver(ArticleObserver):
    anchor_klass = SubSection
    _rules = common_rules(SubSection.name, '[IVX]*')


class ClauseObserver(ArticleObserver):
    anchor_klass = Clause
    _rules = [lambda x: x == '\n', lambda x: re.match('^[IVX]*$', x),
              lambda x: x == '\n']
    number_at = 1
    take_up_to = 2


class SectionObserver(ArticleObserver):
    anchor_klass = Section
    _rules = common_rules(Section.name, '[IVX]*')


class PartObserver(ArticleObserver):
    anchor_klass = Part
    _rules = common_rules(anchor_klass.name, '[IVX]*')


class ChapterObserver(ArticleObserver):
    anchor_klass = Chapter
    _rules = common_rules(Chapter.name, '[IVX]*')


class AnnexObserver(ArticleObserver):
    anchor_klass = Annex
    _rules = common_rules(Annex.name, '[IVX]*')


class UnnumberedAnnexObserver(GenericRuleObserver):
    _rules = [lambda x: x == '\n', lambda x: x == Annex.name, lambda x: x == '\n']

    def replace_in(self, result):
        result[self._index + 2] = Token('')
        result[self._index + 1] = Annex('')


class TitleObserver(ArticleObserver):
    anchor_klass = Title
    _rules = common_rules(Title.name, '[IVX]*')


class NumberObserver(AnchorObserver):
    anchor_klass = Number
    _rules = [lambda x: x == '\n', lambda x: re.match(BASE_NUMBER_REGEX, x),
             lambda x: x == ' ', lambda x: x == '-', lambda x: x == ' ']
    number_at = 1
    take_up_to = 3


class LineObserver(AnchorObserver):
    anchor_klass = Line
    _rules = [lambda x: x == '\n', lambda x: re.match(BASE_LINE_REGEX, x),
              lambda x: x == ' ']
    number_at = 1
    take_up_to = 1
