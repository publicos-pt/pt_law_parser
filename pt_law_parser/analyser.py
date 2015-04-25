import re
from copy import deepcopy
from collections import OrderedDict

from pt_law_parser.core import parser, expressions
from pt_law_parser import constants


class BaseElement(object):

    def __init__(self):
        self._children = []

    def append(self, element):
        self._children.append(element)
        element.set_parent(self)

    def remove(self, element):
        element.clean_parent()
        self._children.remove(element)

    def __getitem__(self, item):
        return self._children[item]

    def __len__(self):
        return len(self._children)

    def as_html(self):
        string = ''
        for child in self._children:
            string += child.as_html()
        return string

    @property
    def text(self):
        string = ''
        for child in self._children:
            string += child.text
        return string


class Document(BaseElement):

    def __init__(self):
        super(Document, self).__init__()


class Element(BaseElement):

    def __init__(self, tag, attrib=None):
        super(Element, self).__init__()
        self.tag = tag
        self._parent = None

        if attrib is None:
            self._attrib = OrderedDict()
        else:
            self._attrib = OrderedDict(attrib)

    @property
    def attrib(self):
        return self._attrib

    def set_parent(self, parent):
        self._parent = parent

    def clean_parent(self):
        self._parent = None

    def as_html(self):
        attributes = ''.join('%s="%s" ' % (key, value)
                             for (key, value) in self._attrib.items())

        return '<{0} {1}>{2}</{0}>'.format(self.tag, attributes,
                                           super(Element, self).as_html())

    def set_id(self, id):
        self.attrib['id'] = id


class Text(Element):

    def __init__(self, text=''):
        assert(isinstance(text, str))
        super(Text, self).__init__('')
        self._text = text

    def __iadd__(self, other):
        assert(isinstance(other, str))
        self._text += other

    def as_html(self):
        return self._text

    @property
    def text(self):
        return self._text


class Reference(Element):

    def __init__(self, reference):
        assert(isinstance(reference, expressions.Reference))
        super(Reference, self).__init__('a', {'href': '#'})
        self._number = reference.string
        self._parent = reference.parent
        self.append(Text(self._number))


class Anchor(Element):

    def __init__(self, anchor):
        assert(isinstance(anchor, expressions.Anchor))
        super(Anchor, self).__init__('p')
        self.append(Text(anchor.name + ' '))
        number = Element('a')
        number.append(Text(anchor.number))
        self.append(number)
        self.anchor_element_index = 1

    def set_href(self, href):
        self[self.anchor_element_index].attrib['href'] = href


class SpanAnchor(Anchor):

    def __init__(self, anchor):
        assert(isinstance(anchor, expressions.Anchor))
        super(Anchor, self).__init__('span')
        number = Element('a')
        number.append(Text(anchor.number))
        self.append(number)
        self.append(Text(' - '))
        self.anchor_element_index = 0


anchor_mapping = {expressions.Number: SpanAnchor,
                  expressions.Article: Anchor}


def parse(text):
    type_names = ['Decreto-Lei', 'Lei', 'Declaração de Rectificação', 'Portaria']

    managers = [
        parser.ObserverManager(dict((name, parser.DocumentsObserver) for name in type_names)),
        parser.ArticleObserverManager(), parser.NumberObserverManager(),
        parser.ObserverManager(dict((name, parser.ArticlesObserver) for name in ['artigo', 'artigos']))]

    terms = {' ', '.', ',', '\n', 'n.os', '«', '»'}
    for manager in managers:
        terms |= manager.terms

    return parser.parse(text, managers, terms)


def analyse(tokens):
    root = Document()
    parser = HierarchyParser(root)

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
            parser.add(block_parser.root)
            paragraph = Element('p')
        # construct the paragraphs
        elif isinstance(token, expressions.Anchor) or token.string == '\n':
            p = parser
            if block_mode:
                p = block_parser
            if len(paragraph):
                p.add(paragraph)
            if isinstance(token, expressions.Anchor):
                p.add(anchor_mapping[type(token)](token))
            paragraph = Element('p')
        else:
            if isinstance(token, expressions.Reference):
                paragraph.append(Reference(token))
            else:
                add_text(token.string)

    return root


class HierarchyParser():
    def __init__(self, root, add_links=True):
        self.current_element = dict([(format, None) for
                                     format in constants.hierarchy_classes])
        self.previous_element = None
        self.root = root
        self._add_links = add_links

    def add(self, paragraph):
        hierarchy_priority = constants.hierarchy_priority

        current_element = self.current_element
        previous_element = self.previous_element

        def add_element(receiving_element, element):
            """
            Adds the current element of `format_to_move` to `receiving_element`.

            If element to add is an element of a list, create a ordered list
            in the receiving element, and add the element to to it.
            """
            # if format_to_move is an item of lists
            if element.tag == 'li':
                # and receiving_element does not have a list, we create it:
                if len(receiving_element) == 0 or receiving_element[-1].tag != 'ol':
                    receiving_element.append(Element('ol'))

                receiving_element = receiving_element[-1]

            receiving_element.append(element)

        def add_element_to_hierarchy(element, format):
            """
            Adds element of format `format_to_move` to the format above in the
            hierarchy, if any.
            """
            for index in reversed(range(0, hierarchy_priority.index(format))):
                format_to_receive = hierarchy_priority[index]

                if current_element[format_to_receive] is not None:
                    add_element(current_element[format_to_receive], element)
                    break
            else:
                add_element(self.root, element)

        def add_id(element, anchor, format):
            assert(isinstance(anchor, Anchor))
            prefix = ''
            for index in reversed(range(constants.formal_hierarchy_elements.index(format))):
                temp_format = constants.formal_hierarchy_elements[index]
                if current_element[temp_format]:
                    prefix = current_element[temp_format].attrib['id'] + '-'
                    break

            suffix = ''
            if format_number:
                suffix = '-' + format_number

            id = prefix + constants.hierarchy_ids[format] + suffix

            element.set_id(id)
            anchor.set_href('#' + id)

        def create_element(element, format):
            # create new tag for `div` or `li`.
            if format in constants.hierarchy_html_lists:
                new_element = Element(constants.hierarchy_html_lists[format],
                                      attrib={'class': constants.hierarchy_classes[format]})
            else:
                new_element = Element('div',
                                      attrib={'class': constants.hierarchy_classes[format]})

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

        if paragraph.tag == 'blockquote':
            for format in reversed(hierarchy_priority):
                if current_element[format] is not None:
                    current_element[format].append(paragraph)
                    break
            else:
                self.root.append(paragraph)
            return  # blockquote added, ignore rest of it.
        for format in hierarchy_priority:
            search = re.search(constants.hierarchy_regex[format], paragraph.text)
            if not search:
                continue
            format_number = search.group(1).strip()

            new_element = create_element(paragraph, format)

            if self._add_links and isinstance(paragraph, Anchor):
                add_id(new_element, paragraph, format)

            add_element_to_hierarchy(new_element, format)

            current_element[format] = new_element
            # reset all current_element in lower hierarchy
            for lower_format in hierarchy_priority[
                                hierarchy_priority.index(format) + 1:]:
                current_element[lower_format] = None
            break
        else:  # is just text
            new_element = deepcopy(paragraph)

            # previous has children and child is an Element with a 'title'
            # => new_element is a title of the previous element.
            if previous_element and len(previous_element) and \
                    isinstance(previous_element[0], Element) and \
                    'title' in previous_element[0].attrib.get("class", []):
                previous_element[0].append(new_element)
            else:
                # add to last non-None format
                for format in reversed(hierarchy_priority):
                    if current_element[format] is not None:
                        current_element[format].append(new_element)
                        break
                else:
                    self.root.append(new_element)

        self.previous_element = new_element
