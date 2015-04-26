from pt_law_parser.core.expressions import *

from pt_law_parser import html

hierarchy_order = [
    Annex, Part, Title, Chapter, Section, SubSection, Article, Number, Line]

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

formal_hierarchy_elements = [Annex, Article, Number, Line]


hierarchy_classes = {Annex: html.AnnexTitle,
                     Part: html.SectionTitle,
                     Title: html.SectionTitle,
                     Chapter: html.SectionTitle,
                     Section: html.SectionTitle,
                     SubSection: html.SectionTitle,
                     Article: html.ArticleTitle,
                     Number: html.NumberTitle,
                     Line: html.LineTitle,
                     }

references = {DocumentReference: html.Reference,
              ArticleReference: html.Reference,
              NumberReference: html.Reference,
              LineReference: html.Reference,
              EULawReference: html.EULawReference,
}
