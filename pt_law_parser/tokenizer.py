from collections import defaultdict

from .expressions import Token, Separator, EndOfLine, Expression


def _tokenize(string, stopchars='', keyterms=()):
    """
    Tokenizes a string into a list of `Token`s separated by `Separator`s and
    ending in a `EndOfString`.

    The string is tokenized using stopchars to separate tokens, but guarantees
    that terms in `keyterms` are maintained.

    In case of multiple key terms matched, it matches the longest one:
    "foo-bar" with keyterms (foo, foo-bar) matches "foo-bar".
    """

    # string_usages: set of terms that are using a given string.
    # usages: the inverse of `string_usages`: which string is used by which term.
    # matches: current terms already matched in sequence
    string_usages = defaultdict(set)
    usages = {}
    matches = set()

    # the lengthier sequence of tokens in use by a term.
    sequence = ''
    sequence_start_index = 0
    for index, char in enumerate(string):
        sequence += char

        for term in keyterms:
            current_string = char
            if term in usages:
                current_string = usages[term] + current_string

            if term not in matches:
                if term.startswith(current_string):
                    # the term uses current_string; update the references list
                    # to current_string.
                    if term in usages:
                        string_usages[usages[term]].remove(term)
                        if not string_usages[usages[term]]:
                            del string_usages[usages[term]]
                    usages[term] = current_string
                    string_usages[current_string].add(term)
                else:  # failed to match current_string.
                    # clean references
                    if term in usages:
                        string_usages[usages[term]].remove(term)
                        if not string_usages[usages[term]]:
                            del string_usages[usages[term]]
                        del usages[term]

            if term == current_string:
                matches.add(term)

        # create a set of candidates
        candidates = set()
        for match in matches:
            assert match in string_usages
            assert match in usages
            if len(string_usages[match]) > 1:
                continue
            invalid = False
            for string in string_usages:
                if string != match and string.startswith(match):
                    invalid = True
                    break
            if invalid:
                continue
            candidates.add(match)

        if candidates:
            # pick the longest candidate
            term = sorted(list(candidates), key=lambda x: len(x), reverse=True)[0]
            prefix, suffix = sequence.split(term)

            if prefix:
                yield Token(prefix)
            yield Token(term)

            sequence = suffix
            for candidate in candidates:
                matches.remove(candidate)
                del string_usages[candidate]
                del usages[candidate]
            sequence_start_index += len(prefix) + len(term)

        # yield non-keyterm tokens.
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
