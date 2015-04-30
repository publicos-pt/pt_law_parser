from pt_law_parser.parser import parse
from pt_law_parser import observers
from pt_law_parser.normalizer import normalize
from pt_law_parser.json import from_json
from pt_law_parser.html import html_toc
import pt_law_parser.analyser


def analyse(text, managers, terms):
    return analyser.analyse(parse(normalize(text), managers, terms))
