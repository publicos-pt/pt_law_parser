from collections import defaultdict

from .expressions import Token, Separator, EndOfLine, Expression


def _tokenize(string, stopchars='', keyterms=()):
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
                    yield Token(rest)

                yield Token(term)
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
                    yield Token(token)
                    sequence_start_index += len(token)
                # yield the stop word
                yield Separator(sequence[0])
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
        yield Token(sequence)
    yield EndOfLine()


def tokenize(string, stopchars='', keyterms=()):
    return Expression(x for x in _tokenize(string, stopchars, keyterms))
