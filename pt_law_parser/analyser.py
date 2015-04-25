from copy import deepcopy

from .html import Document, Element, Text, Reference, Anchor

from pt_law_parser.core import parser, expressions, observers
from pt_law_parser import constants


def parse(text):
    type_names = ['Decreto-Lei', 'Lei', 'Declaração de Rectificação', 'Portaria']

    managers = parser.common_managers + [
        parser.ObserverManager(dict((name, observers.DocumentRefObserver) for name in type_names)),
        parser.ObserverManager(dict((name, observers.ArticleRefObserver) for name in ['artigo', 'artigos']))]

    terms = {' ', '.', ',', '\n', 'n.os', '«', '»'}
    for manager in managers:
        terms |= manager.terms

    return parser.parse(text, managers, terms)


def analyse(tokens):
    root = Document()
    root_parser = HierarchyParser(root)

    def add_text(text):
        if len(paragraph) and isinstance(paragraph[-1], Text):
            el = paragraph[-1]
            el += text
        else:
            paragraph.append(Text(text))

    paragraph = Element('p')

    block_mode = False
    for index, token in enumerate(tokens):
        # start of quote
        if token.string == '«' and len(paragraph) == 0:
            block_mode = True
            block_parser = HierarchyParser(Element('blockquote'), add_links=False)
        # end of quote
        elif token.string == '»' and len(paragraph) == 0:
            block_mode = False
            root_parser.add_blockquote(block_parser.root)
            paragraph = Element('p')
        # construct the paragraphs
        elif isinstance(token, expressions.Anchor) or token.string == '\n':
            p = root_parser
            if block_mode:
                p = block_parser
            if len(paragraph):
                p.add_paragraph(paragraph)

            paragraph = Element('p')
            if isinstance(token, expressions.Anchor):
                anchor_class = constants.hierarchy_classes[type(token)]
                element = anchor_class(token)
                p.add_anchor(element)
                if element.tag == 'span':
                    paragraph = Element('span')
        else:
            if isinstance(token, expressions.Reference):
                paragraph.append(Reference(token))
            else:
                add_text(token.string)

    return root


class HierarchyParser():
    def __init__(self, root, add_links=True):
        self.current_element = dict([(format, None) for
                                     format in constants.hierarchy_order])
        self.previous_element = None
        self.root = root
        self._add_links = add_links

    @staticmethod
    def _add_element(parent, element):
        """
        Adds the current element of `format_to_move` to `parent`.

        If element to add is an element of a list, create a ordered list
        in the receiving element, and add the element to to it.
        """
        # if format_to_move is an item of lists
        if element.tag == 'li':
            # and parent does not have a list, we create it:
            if len(parent) == 0 or parent[-1].tag != 'ol':
                parent.append(Element('ol'))

            parent = parent[-1]

        parent.append(element)

    def _add_element_to_hierarchy(self, element, format):
        """
        Adds element of format `format_to_move` to the format above in the
        hierarchy, if any.
        """
        for index in reversed(range(0, constants.hierarchy_order.index(format))):
            format_to_receive = constants.hierarchy_order[index]

            if self.current_element[format_to_receive] is not None:
                self._add_element(self.current_element[format_to_receive], element)
                break
        else:
            self._add_element(self.root, element)

    def _add_id(self, element, anchor, format):
        assert(isinstance(anchor, Anchor))
        prefix = ''
        for index in reversed(range(constants.formal_hierarchy_elements.index(format))):
            temp_format = constants.formal_hierarchy_elements[index]
            if self.current_element[temp_format]:
                prefix = self.current_element[temp_format].attrib['id'] + '-'
                break

        suffix = ''
        if anchor.number:
            suffix = '-' + anchor.number

        id = prefix + constants.hierarchy_ids[format] + suffix

        element.set_id(id)
        anchor.set_href('#' + id)

    @staticmethod
    def _create_element(element, format):
        # create new tag for `div` or `li`.
        attrib = {'class': constants.html_classes[format]}
        if format in constants.html_lists:
            new_element = Element(constants.html_lists[format], attrib=attrib)
        else:
            new_element = Element('div', attrib=attrib)

        # and put the element in the newly created tag.
        if format in constants.hierarchy_html_titles:
            # if format is title, create it.
            current_element_title = Element(constants.hierarchy_html_titles[format],
                                            attrib={'class': 'title'})
            current_element_title.append(element)

            new_element.append(current_element_title)
        else:
            new_element.append(element)

        return new_element

    def add_blockquote(self, blockquote):
        assert(blockquote.tag == 'blockquote')
        for format in reversed(constants.hierarchy_order):
            if self.current_element[format] is not None:
                self.current_element[format].append(blockquote)
                break
        else:
            self.root.append(blockquote)

    def add_anchor(self, anchor):
        format = anchor.format

        new_element = self._create_element(anchor, format)

        if self._add_links and format in constants.formal_hierarchy_elements:
            self._add_id(new_element, anchor, format)

        self._add_element_to_hierarchy(new_element, format)

        self.current_element[format] = new_element
        # reset all current_element in lower hierarchy
        for lower_format in constants.hierarchy_order[
                constants.hierarchy_order.index(format) + 1:]:
            self.current_element[lower_format] = None

        self.previous_element = new_element

    def add_paragraph(self, paragraph):
        new_element = deepcopy(paragraph)

        # previous has children and child is an Element with a 'title'
        # => new_element is a title of the previous element.
        if self.previous_element and len(self.previous_element) and \
                isinstance(self.previous_element[0], Element) and \
                'title' in self.previous_element[0].attrib.get("class", []):
            self.previous_element[0].append(new_element)
        else:
            # add to last non-None format
            for format in reversed(constants.hierarchy_order):
                if self.current_element[format] is not None:
                    self.current_element[format].append(new_element)
                    break
            else:
                self.root.append(new_element)

        self.previous_element = new_element
