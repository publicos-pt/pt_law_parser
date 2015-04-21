from collections import defaultdict

from .expressions import Token


def tokenize(string, keyterms=()):
    """
    Tokenizes a string into a list of `Token`s.

    The string is tokenized guaranteeing that keyterms are single tokens and
    everything else is a single token.

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
                if string != match and match in string:
                    invalid = True
                    break
            if invalid:
                continue
            candidates.add(match)

        if candidates:
            # pick the longest candidate
            term = sorted(list(candidates), key=lambda x: len(x), reverse=True)[0]
            prefix, suffix = str(sequence).rsplit(term, 1)

            if prefix:
                for token in tokenize(prefix, keyterms):
                    yield token
            yield Token(term)

            # remove all usages that were part of the yielded in term
            for string in dict(string_usages):
                if string in term:
                    for usage in string_usages[string]:
                        del usages[usage]
                    del string_usages[string]
                    if string in matches:
                        matches.remove(string)

            sequence = suffix
            sequence_start_index += len(prefix) + len(term)

    for match in matches:
        prefix, suffix = sequence.split(match)
        yield prefix
        yield match
        sequence = suffix
    if sequence:
        yield Token(sequence)
