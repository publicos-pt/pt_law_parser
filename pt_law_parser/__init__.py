from pt_law_parser.normalizer import normalize
from pt_law_parser.parser import parse, common_managers, ObserverManager
from pt_law_parser import observers
import pt_law_parser.analyser
from pt_law_parser.expressions import from_json
from pt_law_parser.html import html_toc


def analyse(text, managers, terms):
    return analyser.analyse(parse(normalize(text), managers, terms))
