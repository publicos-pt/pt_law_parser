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
        self._ref_class = ref_class
        self._reference = self._ref_class('')
        self._storage = [self._reference]
        self._indexes = {}

    def new_number(self, token, index):
        if self._reference.number:
            self._storage.append(self._ref_class(''))
            self._reference = self._storage[-1]
        self._reference.number = token

        assert index not in self._indexes
        self._indexes[index] = self._reference

    def clear(self):
        self._reference = self._ref_class('')
        self._storage = [self._reference]

    def set_parent(self, temp_parent):
        assert isinstance(temp_parent, TempStorage)
        for ref in self._storage:
            ref.parent = temp_parent._reference

    def replace_in(self, result):
        for index in self._indexes:
            result[index] = self._indexes[index]


class DocTempStorage(TempStorage):
    def __init__(self):
        self._parent = None
        super(DocTempStorage, self).__init__(DocumentReference)

    def set_parent(self, token):
        self._parent = token

    def new_number(self, token, index):
        self._reference.parent = self._parent
        super(DocTempStorage, self).new_number(token, index)
        self._reference.parent = self._parent


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

            temp_storage['lin'].replace_in(result)

            line_state.clear()
            temp_storage['lin'].clear()
            logger.debug('changed to line.%s' % line_state.current)

        if number_state.isstate('single') and \
                (token == '' or article_state.isstate('single')):
            if article_state.isstate('single'):
                temp_storage['num'].set_parent(temp_storage['art'])

            temp_storage['num'].replace_in(result)

            number_state.clear()
            temp_storage['num'].clear()
            logger.debug('changed to number.%s' % number_state.current)

        if article_state.isstate('single') and \
                (token == '' or document_state.isstate('single')):
            if document_state.isstate('single'):
                temp_storage['art'].set_parent(temp_storage['doc'])

            temp_storage['art'].replace_in(result)

            article_state.clear()
            temp_storage['art'].clear()
            logger.debug('changed to article.%s' % article_state.current)

        if document_state.isstate('single') and token == '':
            temp_storage['doc'].replace_in(result)

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

    return result
