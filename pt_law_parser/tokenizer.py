from pt_law_parser import _tokenizer

from pt_law_parser.expressions import Token


def tokenize(string, keyterms=()):
    return [Token(token) for token in _tokenizer.tokenize(string, keyterms)]
