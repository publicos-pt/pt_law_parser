"""
Contains the function `analyse`, that transforms a linear sequence of expressions
into a tree structure of sections.
"""
from pt_law_parser.expressions import Annex, Part, Title, Chapter, Section, \
    SubSection, Article, Number, Line, Item, Paragraph, Anchor, QuotationSection, Clause, \
    Document, InlineParagraph, InlineDocumentSection, TitledDocumentSection, \
    Token, UnorderedDocumentSection, OrderedDocumentSection

hierarchy_order = [
    Annex, Part, Title, Chapter, Section, SubSection, Clause, Article, Number,
    Line, Item,
]

# formats that only take one paragraph
single_paragraph_format = {Item}


def analyse(tokens):
    root = Document()
    root_parser = HierarchyParser(root)

    paragraph = Paragraph()
    block_mode = False
    for token in tokens:
        if token.as_str() == '':
            continue
        # start of quote
        if token == Token('«') and len(paragraph) == 0:
            block_mode = True
            block_parser = HierarchyParser(QuotationSection(), add_links=False)
        # end of quote
        elif token == Token('»') and len(paragraph) == 0:
            block_mode = False
            root_parser.add(block_parser.root)
            paragraph = Paragraph()
        # construct the paragraphs
        # paragraph can end by '\n' or by starting a new section.
        elif isinstance(token, Anchor) or token.string == '\n':
            # it is end of paragraph; complete it if it ends by a normal \n.
            if token.string == '\n':
                paragraph.append(token)

            # select current parser
            p = root_parser
            if block_mode:
                p = block_parser

            # add paragraph to the current parser if it is not empty
            if len(paragraph):
                p.add(paragraph)

            # start a new paragraph
            paragraph = Paragraph()
            if isinstance(token, Anchor):
                # create a new section
                section = p.new_section(token)

                # if new new section is inline, change to inline paragraph
                if isinstance(section, InlineDocumentSection):
                    paragraph = InlineParagraph()
        else:
            paragraph.append(token)

    return root


class HierarchyParser():
    def __init__(self, root, add_links=True):
        self.current_element = dict([(format, None) for
                                     format in hierarchy_order])
        self.root = root
        self._add_links = add_links

    def _add_element_to_hierarchy(self, element, format):
        """
        Adds `element` to the `format` in the hierarchy, if any.
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
        elif anchor.format in OrderedDocumentSection.formats:
            return OrderedDocumentSection(anchor)
        elif anchor.format in UnorderedDocumentSection.formats:
            return UnorderedDocumentSection(anchor)

    def add(self, element):
        for format in reversed(hierarchy_order):
            if self.current_element[format] is not None:
                # decide if we add paragraph as title or not.
                needs_title = (isinstance(self.current_element[format],
                                          TitledDocumentSection) and
                               self.current_element[format].title is None and
                               len(self.current_element[format]) == 0)
                if isinstance(element, Paragraph) and needs_title:
                    self.current_element[format].title = element
                else:
                    self.current_element[format].append(element)
                    if format in single_paragraph_format:
                        self.current_element[format] = None
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
