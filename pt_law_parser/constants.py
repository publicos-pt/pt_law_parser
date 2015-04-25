from pt_law_parser.core.expressions import *

from pt_law_parser import html

hierarchy_order = [
    Annex, Part, Title, Chapter, Section, SubSection, Article, Number, Line]

html_classes = {Annex: 'annex',
                Part: 'part',
                Title: 'title',
                Chapter: 'chapter',
                Section: 'section',
                SubSection: 'sub-section',
                Article: 'article',
                Number: 'number list-unstyled',
                Line: 'line list-unstyled'}

hierarchy_ids = {Annex: 'anexo',
                 Part: 'parte',
                 Title: 'titulo',
                 Chapter: 'capitulo',
                 Section: 'seccao',
                 SubSection: 'subseccao',
                 Article: 'artigo',
                 Number: 'numero',
                 Line: 'alinea'}

hierarchy_html_titles = {Part: 'h2',
                         Title: 'h3',
                         Chapter: 'h3',
                         Section: 'h4',
                         SubSection: 'h5',
                         Annex: 'h2',
                         Article: 'h5'}

html_lists = {Number: 'li', Line: 'li'}

formal_hierarchy_elements = [Annex, Article, Number, Line]


hierarchy_classes = {Annex: html.Annex,
                     Part: html.Section,
                     Title: html.Section,
                     Chapter: html.Section,
                     Section: html.Section,
                     SubSection: html.Section,
                     Article: html.Article,
                     Number: html.Number,
                     Line: html.Line,
                     }
