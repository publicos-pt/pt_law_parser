import re
import logging

from fysom import Fysom

from .tokenizer import tokenize
from .expressions import Separator, Expression, Reference, ArticleReference,\
    NumberReference, LineReference


DOCUMENT_NUMBER_REGEX = '^[\d\-A-Z]+/\d+(?:/[A-Z]*)?$'
ARTICLE_NUMBER_REGEX = '^[\dA-Z\-]+º(?:\-[A-Z]+)?$|^anterior$|^seguinte$'
NUMBER_REGEX = '^\d$|^anterior$|^seguinte$'
LINE_REGEX = '^[\da-z]*\)$'


def parse(string, singular_names, plural_names):
    common_events = [('single',  'None', 'single'), ('many', 'None', 'many'),
                     ('last', 'many', 'single'), ('clear', 'single', 'None')]

    document_state = Fysom(initial='None', events=common_events)
    article_state = Fysom(initial='None', events=common_events)
    number_state = Fysom(initial='None', events=common_events)
    line_state = Fysom(initial='None', events=common_events)

    logger = logging.getLogger(__name__ + '.organize_string')

    doc_storage = {'type_name': None, 'numbers': []}
    doc_reference = Reference('', '')
    doc_ref_storage = [doc_reference]
    art_storage = {'numbers': [], 'document': None}
    art_reference = ArticleReference('')
    art_ref_storage = [art_reference]
    num_storage = {'numbers': [], 'article': None}
    num_reference = NumberReference('')
    num_ref_storage = [num_reference]
    lin_storage = {'lines': [], 'parent': None}
    lin_reference = LineReference('')
    lin_ref_storage = [lin_reference]

    storage = {'documents': [], 'articles': [], 'numbers': [], 'lines': []}

    def check_doc_format(token):
        if document_state.isstate('single'):
            if not doc_storage['numbers'] and token != doc_storage['type_name']:
                assert(token == 'nº')
        elif document_state.isstate('many'):
            if not doc_storage['numbers'] and token != doc_storage['type_name']:
                assert(token == 'n.os')

    def start_document(token):
        if token.as_str() in singular_names:
            document_state.single()
            doc_storage['type_name'] = token
            doc_reference.type = token
            logger.debug('changed to document.%s' % document_state.current)
        if token.as_str() in plural_names:
            document_state.many()
            doc_storage['type_name'] = token
            doc_reference.type = token
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
            if doc_reference.number:
                doc_ref_storage.append(Reference(doc_reference.type, ''))
                doc_reference = doc_ref_storage[-1]
            doc_reference.index = index
            doc_reference.number = token
            doc_storage['numbers'].append(token)

        if re.match(ARTICLE_NUMBER_REGEX, token.as_str()) and not article_state.isstate('None'):
            if art_reference.number:
                art_ref_storage.append(ArticleReference(''))
                art_reference = art_ref_storage[-1]
            art_reference.index = index
            art_reference.number = token
            art_storage['numbers'].append(token)

        if re.match(NUMBER_REGEX, token.as_str()) and not number_state.isstate('None'):
            if num_reference.number:
                num_ref_storage.append(NumberReference(''))
                num_reference = num_ref_storage[-1]
            num_reference.index = index
            num_reference.number = token
            num_storage['numbers'].append(token)

        if re.match(LINE_REGEX, token.as_str()) and not line_state.isstate('None'):
            if lin_reference.number:
                lin_ref_storage.append(LineReference(''))
                lin_reference = lin_ref_storage[-1]
            lin_reference.index = index
            lin_reference.number = token
            lin_storage['lines'].append(token)

        # checker
        check_doc_format(token)

        # storage and clear
        if line_state.isstate('single') and \
                (token == '' or article_state.isstate('single') or
                 number_state.isstate('single')):
            if number_state.isstate('single'):
                lin_storage['parent'] = num_storage
            elif article_state.isstate('single'):
                lin_storage['parent'] = art_storage

            storage['lines'].append(lin_storage)

            line_state.clear()
            lin_storage = {'numbers': [], 'parent': None}
            lin_reference = LineReference('')
            lin_ref_storage = [lin_reference]
            logger.debug('changed to line.%s' % line_state.current)

        if number_state.isstate('single') and \
                (token == '' or article_state.isstate('single')):
            if article_state.isstate('single'):
                num_storage['article'] = art_storage

            for ref in num_ref_storage:
                if article_state.isstate('single'):
                    ref.parent = art_reference
                result[ref.index] = ref
                del ref.index

            storage['numbers'].append(num_storage)

            number_state.clear()
            num_storage = {'numbers': [], 'article': None}
            num_reference = NumberReference('')
            num_ref_storage = [num_reference]
            logger.debug('changed to number.%s' % number_state.current)

        if article_state.isstate('single') and \
                (token == '' or document_state.isstate('single')):
            if document_state.isstate('single'):
                art_storage['document'] = doc_storage

            for ref in art_ref_storage:
                if document_state.isstate('single'):
                    ref.parent = doc_reference
                result[ref.index] = ref
                del ref.index

            storage['articles'].append(art_storage)

            article_state.clear()
            art_storage = {'numbers': [], 'document': None}
            art_reference = ArticleReference('')
            art_ref_storage = [art_reference]
            logger.debug('changed to article.%s' % article_state.current)

        if document_state.isstate('single') and token == '':
            storage['documents'].append(doc_storage)
            for ref in doc_ref_storage:
                result[ref.index] = ref
                del ref.index

            document_state.clear()
            doc_storage = {'type_name': None, 'numbers': []}
            doc_reference = Reference('', '')
            doc_ref_storage = [doc_reference]
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
