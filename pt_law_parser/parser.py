import re
import logging

from fysom import Fysom

from .tokenizer import tokenize
from .expressions import Separator, Expression, DocumentReference, ArticleReference,\
    NumberReference, LineReference


DOCUMENT_NUMBER_REGEX = '^[\d\-A-Z]+/\d+(?:/[A-Z]*)?$'
ARTICLE_NUMBER_REGEX = '^[\dA-Z\-]+º(?:\-[A-Z]+)?$|^anterior$|^seguinte$'
NUMBER_REGEX = '^\d$|^anterior$|^seguinte$'
LINE_REGEX = '^[\da-z]*\)$'


class TempStorage(object):
    def __init__(self, ref_class):
        self.ref_class = ref_class
        self.storage = {'numbers': [], 'parent': None}
        self.reference = self.ref_class('')
        self.ref_storage = [self.reference]

    def new_number(self, token, index):
        if self.reference.number:
            self.ref_storage.append(self.ref_class(''))
            self.reference = self.ref_storage[-1]
        self.reference.index = index
        self.reference.number = token
        self.storage['numbers'].append(token)

    def clear(self):
        self.storage = {'numbers': [], 'parent': None}
        self.reference = self.ref_class('')
        self.ref_storage = [self.reference]

    def set_parent(self, temp_parent):
        assert isinstance(temp_parent, TempStorage)
        self.storage['parent'] = temp_parent.storage
        for ref in self.ref_storage:
            ref.parent = temp_parent.reference


class DocTempStorage(TempStorage):
    def __init__(self):
        self._parent = None
        super(DocTempStorage, self).__init__(DocumentReference)

    def set_parent(self, token):
        self._parent = token
        self.storage['parent'] = token

    def new_number(self, token, index):
        self.reference.parent = self._parent
        super(DocTempStorage, self).new_number(token, index)
        self.reference.parent = self._parent


def parse(string, singular_names, plural_names):
    common_events = [('single',  'None', 'single'), ('many', 'None', 'many'),
                     ('last', 'many', 'single'), ('clear', 'single', 'None')]

    document_state = Fysom(initial='None', events=common_events)
    article_state = Fysom(initial='None', events=common_events)
    number_state = Fysom(initial='None', events=common_events)
    line_state = Fysom(initial='None', events=common_events)

    logger = logging.getLogger(__name__ + '.organize_string')

    temp_storage = {'doc': DocTempStorage(),
                    'art': TempStorage(ArticleReference),
                    'num': TempStorage(NumberReference),
                    'lin': TempStorage(LineReference),
                    }

    storage = {'documents': [], 'articles': [], 'numbers': [], 'lines': []}

    def start_document(token):
        if token.as_str() in singular_names:
            document_state.single()
            temp_storage['doc'].set_parent(token)
            logger.debug('changed to document.%s' % document_state.current)
        if token.as_str() in plural_names:
            document_state.many()
            temp_storage['doc'].set_parent(token)
            logger.debug('changed to document.%s' % document_state.current)

    def start_article(token):
        if token.as_str() in ('artigo', 'Artigo'):
            article_state.single()
            logger.debug('changed to article.%s' % article_state.current)
        if token.as_str() in ('artigos', 'Artigos'):
            article_state.many()
            logger.debug('changed to article.%s' % article_state.current)

    def start_number(token):
        # nº and n.os is also for document. Ignore if document is on.
        if not document_state.isstate('None'):
            return
        if token.as_str() == 'nº':
            number_state.single()
            logger.debug('changed to number.%s' % number_state.current)
        if token.as_str() == 'n.os':
            number_state.many()
            logger.debug('changed to number.%s' % number_state.current)

    def start_line(token):
        # nº and n.os is also for document. Ignore if document is on.
        if token.as_str() in ('alínea', 'Alínea'):
            line_state.single()
            logger.debug('changed to line.%s' % line_state.current)
        if token.as_str() in ('alíneas', 'Alíneas'):
            line_state.many()
            logger.debug('changed to line.%s' % line_state.current)

    result = Expression()
    for index, token in enumerate(tokenize(string, ' ,.', {'n.os'} | set(singular_names) | set(plural_names))):
        result.append(token)
        if isinstance(token, Separator):
            continue
        logger.debug(token)
        start_document(token)
        start_article(token)
        start_number(token)
        start_line(token)

        if re.match(DOCUMENT_NUMBER_REGEX, token.as_str()):
            assert not document_state.isstate('None')
            temp_storage['doc'].new_number(token, index)

        if re.match(ARTICLE_NUMBER_REGEX, token.as_str()) and not article_state.isstate('None'):
            temp_storage['art'].new_number(token, index)

        if re.match(NUMBER_REGEX, token.as_str()) and not number_state.isstate('None'):
            temp_storage['num'].new_number(token, index)

        if re.match(LINE_REGEX, token.as_str()) and not line_state.isstate('None'):
            temp_storage['lin'].new_number(token, index)

        # storage and clear
        if line_state.isstate('single') and \
                (token == '' or article_state.isstate('single') or
                 number_state.isstate('single')):
            if number_state.isstate('single'):
                temp_storage['lin'].set_parent(temp_storage['num'])
            elif article_state.isstate('single'):
                temp_storage['lin'].set_parent(temp_storage['art'])

            storage['lines'].append(temp_storage['lin'].storage)

            for ref in temp_storage['lin'].ref_storage:
                result[ref.index] = ref
                del ref.index

            line_state.clear()
            temp_storage['lin'].clear()
            logger.debug('changed to line.%s' % line_state.current)

        if number_state.isstate('single') and \
                (token == '' or article_state.isstate('single')):
            if article_state.isstate('single'):
                temp_storage['num'].set_parent(temp_storage['art'])

            for ref in temp_storage['num'].ref_storage:
                result[ref.index] = ref
                del ref.index

            storage['numbers'].append(temp_storage['num'].storage)

            number_state.clear()
            temp_storage['num'].clear()
            logger.debug('changed to number.%s' % number_state.current)

        if article_state.isstate('single') and \
                (token == '' or document_state.isstate('single')):
            if document_state.isstate('single'):
                temp_storage['art'].set_parent(temp_storage['doc'])

            for ref in temp_storage['art'].ref_storage:
                result[ref.index] = ref
                del ref.index

            storage['articles'].append(temp_storage['art'].storage)

            article_state.clear()
            temp_storage['art'].clear()
            logger.debug('changed to article.%s' % article_state.current)

        if document_state.isstate('single') and token == '':
            for ref in temp_storage['doc'].ref_storage:
                result[ref.index] = ref
                del ref.index

            storage['documents'].append(temp_storage['doc'].storage)

            document_state.clear()
            temp_storage['doc'].clear()
            logger.debug('changed to document.%s' % document_state.current)

        # change from many -> last
        if line_state.isstate('many') and token == 'e':
            line_state.last()
            logger.debug('changed to line.%s' % line_state.current)

        if number_state.isstate('many') and token == 'e':
            number_state.last()
            logger.debug('changed to number.%s' % number_state.current)

        if article_state.isstate('many') and token == 'e':
            article_state.last()
            logger.debug('changed to article.%s' % article_state.current)

        if document_state.isstate('many') and token == 'e':
            document_state.last()
            logger.debug('changed to document.%s' % document_state.current)

    return storage
