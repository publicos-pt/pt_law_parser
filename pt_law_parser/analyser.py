from pt_law_parser.core.expressions import Annex, Part, Title, Chapter, Section, \
    SubSection, Article, Number, Line, Paragraph, Anchor, QuotationSection, \
    Document, InlineParagraph, InlineDocumentSection, TitledDocumentSection
from pt_law_parser.core import parser, observers

hierarchy_order = [
    Annex, Part, Title, Chapter, Section, SubSection, Article, Number, Line]


def parse(text):
    type_names = ['Decreto-Lei', 'Lei', 'Declaração de Rectificação', 'Portaria']

    managers = parser.common_managers + [
        parser.ObserverManager(dict((name, observers.DocumentRefObserver)
                                    for name in type_names)),
        parser.ObserverManager(dict((name, observers.ArticleRefObserver)
                                    for name in ['artigo', 'artigos']))]

    terms = {' ', '.', ',', '\n', 'n.os', '«', '»'}
    for manager in managers:
        terms |= manager.terms

    return parser.parse(text, managers, terms)


def analyse(tokens):
    root = Document()
    root_parser = HierarchyParser(root)

    paragraph = Paragraph()
    block_mode = False
    for token in tokens:
        if token.string == '':
            continue
        # start of quote
        if token.string == '«' and len(paragraph) == 0:
            block_mode = True
            block_parser = HierarchyParser(QuotationSection(), add_links=False)
        # end of quote
        elif token.string == '»' and len(paragraph) == 0:
            block_mode = False
            root_parser.add(block_parser.root)
            paragraph = Paragraph()
        # construct the paragraphs
        elif isinstance(token, Anchor) or token.string == '\n':
            if token.string == '\n':
                paragraph.append(token)
            p = root_parser
            if block_mode:
                p = block_parser
            if len(paragraph):
                p.add(paragraph)

            paragraph = Paragraph()
            if isinstance(token, Anchor):
                section = p.new_section(token)
                if isinstance(section, InlineDocumentSection):
                    paragraph = InlineParagraph()
        else:
            paragraph.append(token)

    return root


class HierarchyParser():
    def __init__(self, root, add_links=True):
        self.current_element = dict([(element, None) for
                                     element in hierarchy_order])
        self.root = root
        self._add_links = add_links

    def _add_element_to_hierarchy(self, element, format):
        """
        Adds element of format `format_to_move` to the format above in the
        hierarchy, if any.
        """
        for index in reversed(range(hierarchy_order.index(format))):
            format_to_receive = hierarchy_order[index]

            if self.current_element[format_to_receive] is not None:
                self.current_element[format_to_receive].append(element)
                break
        else:
            self.root.append(element)

    @staticmethod
    def _create_section(anchor):
        if anchor.format in TitledDocumentSection.hierarchy_html_titles:
            return TitledDocumentSection(anchor)
        elif anchor.format in InlineDocumentSection.html_lists:
            return InlineDocumentSection(anchor)

    def add(self, element):
        for format in reversed(hierarchy_order):
            if self.current_element[format] is not None:
                self.current_element[format].append(element)
                break
        else:
            self.root.append(element)

    def new_section(self, anchor):
        format = anchor.format

        new_element = self._create_section(anchor)

        self._add_element_to_hierarchy(new_element, format)

        self.current_element[format] = new_element
        # reset all current_element in lower hierarchy
        for lower_format in hierarchy_order[hierarchy_order.index(format) + 1:]:
            self.current_element[lower_format] = None

        return new_element
