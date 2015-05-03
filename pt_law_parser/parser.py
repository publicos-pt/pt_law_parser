"""
Contains the `parse` function and auxiliary classes. With the help of observers,
`parse` transforms a list of independent `Token`s into a list of other expressions.
"""

from pt_law_parser import observers
from pt_law_parser.tokenizer import tokenize


class ObserverManager(object):
    def __init__(self, rules):
        self._rules = rules
        self._observers = {}

        # A cache, see _refresh_items. This optimization was pre-profiled.
        # It save us ~30% on analysing doc_id=640339.
        self._items = {}

    def _refresh_items(self):
        self._items = sorted(dict(self._observers).items(), reverse=True)

    def generate(self, index, token):
        if token.as_str() in self._rules:
            observer = self._rules[token.as_str()](index, token)
            self._observers[index] = observer
            self._refresh_items()

    @property
    def terms(self):
        return set(self._rules.keys())

    def observe(self, index, token, caught):
        for i, observer in self._items:
            caught = observer.observe(index, token, caught) or caught
        return caught

    def replace_in(self, result):
        did_change = False
        for i, observer in self._items:
            if observer.is_done:
                if observer.needs_replace:
                    observer.replace_in(result)
                del self._observers[i]
                did_change = True
        if did_change:
            self._refresh_items()

    def finish(self, result):
        for i, observer in self._items:
            observer.finish()
            if observer.needs_replace:
                observer.replace_in(result)
            del self._observers[i]
        self._refresh_items()


def parse(string, managers, terms=set()):
    """
    Parses a string into a list of expressions. Uses managers to replace `Token`s
    by other elements.
    """
    result = []  # the end result

    for manager in managers:
        terms |= manager.terms

    for index, token in enumerate(tokenize(string, terms)):
        result.append(token)

        caught = False
        for manager in managers:
            manager.generate(index, token)
            caught = manager.observe(index, token, caught) or caught
            manager.replace_in(result)

    for manager in managers:
        manager.finish(result)

    return result


common_managers = [
    ObserverManager({'Diretiva': observers.EULawRefObserver,
                     'Decisão de Execução': observers.EULawRefObserver}),
    ObserverManager({'\n': observers.AnnexObserver}),
    ObserverManager({'\n': observers.UnnumberedAnnexObserver}),
    ObserverManager({'\n': observers.SectionObserver}),
    ObserverManager({'\n': observers.SubSectionObserver}),
    ObserverManager({'\n': observers.ClauseObserver}),
    ObserverManager({'\n': observers.PartObserver}),
    ObserverManager({'\n': observers.TitleObserver}),
    ObserverManager({'\n': observers.ChapterObserver}),
    ObserverManager({'\n': observers.ArticleObserver}),
    ObserverManager({'\n': observers.NumberObserver}),
    ObserverManager({'\n': observers.LineObserver}),
]
