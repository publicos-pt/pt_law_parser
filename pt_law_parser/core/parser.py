from pt_law_parser.core import observers
from .tokenizer import tokenize


class ObserverManager(object):
    def __init__(self, rules):
        self._rules = rules
        self._observers = {}

    def generate(self, index, token):
        if token.as_str() in self._rules:
            observer = self._rules[token.as_str()](index, token)
            self._observers[index] = observer

    @property
    def terms(self):
        return set(self._rules.keys())

    def _items(self):
        return sorted(dict(self._observers).items(), reverse=True)

    def observe(self, index, token, caught):
        for i, observer in self._items():
            caught = observer.observe(index, token, caught) or caught
        return caught

    def replace_in(self, result):
        for i, observer in self._items():
            if observer.is_done:
                if observer.needs_replace:
                    observer.replace_in(result)
                del self._observers[i]

    def finish(self, result):
        for i, observer in self._items():
            observer.finish()
            if observer.needs_replace:
                observer.replace_in(result)
            del self._observers[i]


def parse(string, managers, terms=set()):
    result = []

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
    ObserverManager({'\n': observers.PartObserver}),
    ObserverManager({'\n': observers.TitleObserver}),
    ObserverManager({'\n': observers.ChapterObserver}),
    ObserverManager({'\n': observers.ArticleObserver}),
    ObserverManager({'\n': observers.NumberObserver}),
    ObserverManager({'\n': observers.LineObserver}),
]
