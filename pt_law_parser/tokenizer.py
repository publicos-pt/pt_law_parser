"""
This module contains pure Python methods to parse the law text.
"""
import re
import logging
from collections import defaultdict

from fysom import Fysom  # for a finite state machine


def normalize(text):

    text = ' '.join(text.split())

    ## to substitute <br/> by </p><p>
    text = text.replace("<br />", "<br/>")
    text = text.replace("<br/>", "</p><p>")
    text = text.replace("<br >", "<br>")
    text = text.replace("<br>", "</p><p>")

    ## strip inside tags
    text = text.replace('<p> ', '<p>')
    text = text.replace(' </p>', '</p>')

    text = text.replace('ARTIGO', 'Artigo')
    text = text.replace('PARTE', 'Parte')
    text = text.replace('TÍTULO', 'Título')
    text = text.replace('CAPÍTULO', 'Capítulo')
    text = text.replace('SECÇÃO', 'Secção')
    text = text.replace('ANEXO', 'Anexo')

    # older documents use "Art." instead of "Artigo"; change it
    text = re.sub('Art\. (\d+)\.º (.*?)',
                  lambda m: "Artigo %s.º %s" % m.group(1, 2),
                  text)

    # older documents use "Artigo #.º - 1 -" instead of "Artigo #.º 1 -"; change it
    text = re.sub('Artigo (\d+)\.º - (.*?)',
                  lambda m: "Artigo %s.º %s" % m.group(1, 2),
                  text)

    # create <p>'s specifically for start of articles
    text = re.sub("<p>Artigo (\d+)\.º (.*?)</p>",
                  lambda m: "<p>Artigo %s.º</p><p>%s</p>" % m.group(1, 2),
                  text)

    ## add blockquote to changes
    text = text.replace('» </p>', '»</p>')
    text = text.replace(r'<p> «', r'<p>«')

    text = re.sub("<p>«(.*?)»</p>",
                  lambda m: "<blockquote><p>%s</p></blockquote>" % m.group(1),
                  text, flags=re.MULTILINE)

    # normalize bullets to "# -" (substituting the ones using #.)
    text = re.sub(r"<p>(\d+)\.",
                  lambda m: "<p>%s -" % m.group(1),
                  text)

    # normalize ".º" to "º"
    text = text.replace('.º', 'º')

    return text


DOCUMENT_NUMBER_REGEX = '^[\d\-A-Z]+/\d+(?:/[A-Z]*)?$'
ARTICLE_NUMBER_REGEX = '^[\dA-Z\-]+º(?:\-[A-Z]+)?$|^anterior$|^seguinte$'
NUMBER_REGEX = '^\d$|^anterior$|^seguinte$'
LINE_REGEX = '^[\da-z]*\)$'


class Token(object):
    """
    A token result of the tokenization. Stores the token and its position
    on the string.
    """
    def __init__(self, string, index):
        self._string = string
        self._index = index

    @property
    def string(self):
        return self._string

    @property
    def index(self):
        return self._index

    @property
    def end(self):
        return self._index + len(self._string)

    def __eq__(self, other):
        if isinstance(other, str):
            return self._string == other
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))

    def __repr__(self):
        return '<%s %s %d>' % (self.__class__.__name__, repr(self._string), self._index)


class Separator(Token):
    pass


class EndOfString(Token):
    pass


def tokenize(string, stopchars='', keyterms=()):
    """
    Tokenizes a string into a list of `Token`s separated by `Separator`s and
    ending in a `EndOfString`.

    The string is tokenized using stopchars to separate tokens, but guarantees
    that terms in `keyterms` are maintained. Example:

    >>> tokenize('a b a ba a c', ' ', 'd a')
    >>> ['a b', ' ', 'a b', 'a', ' ', 'a', ' ', 'c']
    """
    keyterms = list(keyterms)

    def sorter(term):
        total = 0
        for x in stopchars:
            total += term.count(x)
        return total, len(term)

    keyterms.sort(key=sorter, reverse=True)
    print(keyterms)

    # stores the set of terms that are using a given string.
    string_usages = defaultdict(set)
    # stores the inverse of `string_usages`: string used by term.
    usages = {}

    # the lengthier sequence of tokens in use by a term.
    sequence = ''
    sequence_start_index = 0
    for index, char in enumerate(string):
        sequence += char

        for term in keyterms:
            current_string = char
            if term in usages:
                current_string = usages[term] + current_string

            # the term matches exactly the list of tokens.
            if term == current_string:
                term_index = index + 1 - len(term)
                # if the sequence is not the current string, we must
                # yield the missing part first.
                if sequence != current_string:
                    rest = sequence[:-len(term)]
                    yield Token(rest, term_index - len(rest))

                yield Token(term, term_index)
                # clean all references and sequence
                string_usages = defaultdict(set)
                usages = {}
                sequence = ''
                sequence_start_index = index + 1
                break
            else:
                if term.startswith(current_string):
                    # the term uses current_string; update the references list
                    # to current_string.
                    if term in usages:
                        string_usages[usages[term]].remove(term)
                    usages[term] = current_string
                    string_usages[current_string].add(term)
                else:  # failed to match current_string.
                    # clean references
                    if term in usages:
                        string_usages[usages[term]].remove(term)
                        if not string_usages[usages[term]]:
                            del string_usages[usages[term]]
                        del usages[term]

        token = ''
        backup = sequence
        backup_index = sequence_start_index
        while sequence and sequence not in string_usages:
            if sequence[0] in stopchars:
                # yield the term
                if token:
                    yield Token(token, sequence_start_index)
                    sequence_start_index += len(token)
                # yield the stop word
                yield Separator(sequence[0], sequence_start_index)
                sequence_start_index += 1

                # move the backup
                chars_move = len(token) + 1
                backup = backup[chars_move:]
                backup_index += chars_move
                token = ''
            else:
                token += sequence[0]
            sequence = sequence[1:]
        sequence = backup
        sequence_start_index = backup_index

    if sequence:
        yield Token(sequence, index + 1 - len(sequence))
    yield EndOfString('', index + 1)


def parse_string(string, singular_names, plural_names):
    common_events = [('single',  'None', 'single'), ('many', 'None', 'many'),
                     ('last', 'many', 'single'), ('clear', 'single', 'None')]

    document_state = Fysom(initial='None', events=common_events)
    article_state = Fysom(initial='None', events=common_events)
    number_state = Fysom(initial='None', events=common_events)
    line_state = Fysom(initial='None', events=common_events)

    logger = logging.getLogger(__name__ + '.organize_string')

    doc_storage = {'type_name': None, 'numbers': []}
    art_storage = {'numbers': [], 'document': None}
    num_storage = {'numbers': [], 'article': None}
    lin_storage = {'lines': [], 'parent': None}

    storage = {'documents': [], 'articles': [], 'numbers': [], 'lines': []}

    def check_doc_format(token):
        if document_state.isstate('single'):
            if not doc_storage['numbers'] and token != doc_storage['type_name']:
                assert(token == 'nº')
        elif document_state.isstate('many'):
            if not doc_storage['numbers'] and token != doc_storage['type_name']:
                assert(token == 'n.os')

    def start_document(token):
        if token.string in singular_names:
            document_state.single()
            doc_storage['type_name'] = token
            logger.debug('changed to document.%s' % document_state.current)
        if token.string in plural_names:
            document_state.many()
            doc_storage['type_name'] = token
            logger.debug('changed to document.%s' % document_state.current)

    def start_article(token):
        if token.string in ('artigo', 'Artigo'):
            article_state.single()
            logger.debug('changed to article.%s' % article_state.current)
        if token.string == 'artigos':
            article_state.many()
            logger.debug('changed to article.%s' % article_state.current)

    def start_number(token):
        # n.º and n.os is also for document. Ignore if document is on.
        if not document_state.isstate('None'):
            return
        if token.string == 'nº':
            number_state.single()
            logger.debug('changed to number.%s' % number_state.current)
        if token.string == 'n.os':
            number_state.many()
            logger.debug('changed to number.%s' % number_state.current)

    def start_line(token):
        # nº and n.os is also for document. Ignore if document is on.
        if token.string in ('alínea', 'Alínea'):
            line_state.single()
            logger.debug('changed to line.%s' % line_state.current)
        if token.string in ('alíneas', 'Alíneas'):
            line_state.many()
            logger.debug('changed to line.%s' % line_state.current)

    for token in tokenize(string, ' ,.', {'n.os'} | set(singular_names) | set(plural_names)):
        if isinstance(token, Separator):
            continue
        logger.debug(token)
        start_document(token)
        start_article(token)
        start_number(token)
        start_line(token)

        if re.match(DOCUMENT_NUMBER_REGEX, token.string):
            assert not document_state.isstate('None')
            doc_storage['numbers'].append(token)

        if re.match(ARTICLE_NUMBER_REGEX, token.string) and not article_state.isstate('None'):
            art_storage['numbers'].append(token)

        if re.match(NUMBER_REGEX, token.string) and not number_state.isstate('None'):
            assert not number_state.isstate('None')
            num_storage['numbers'].append(token)

        if re.match(LINE_REGEX, token.string) and not line_state.isstate('None'):
            assert not line_state.isstate('None')
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
            logger.debug('changed to line.%s' % line_state.current)

        if number_state.isstate('single') and \
                (token == '' or article_state.isstate('single')):
            if article_state.isstate('single'):
                num_storage['article'] = art_storage

            storage['numbers'].append(num_storage)

            number_state.clear()
            num_storage = {'numbers': [], 'article': None}
            logger.debug('changed to number.%s' % number_state.current)

        if article_state.isstate('single') and \
                (token == '' or document_state.isstate('single')):
            if document_state.isstate('single'):
                art_storage['document'] = doc_storage

            storage['articles'].append(art_storage)

            article_state.clear()
            art_storage = {'numbers': [], 'document': None}
            logger.debug('changed to article.%s' % article_state.current)

        if document_state.isstate('single') and token  == '':
            storage['documents'].append(doc_storage)

            document_state.clear()
            doc_storage = {'type_name': None, 'numbers': []}
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
