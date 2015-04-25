from pt_law_parser.html import Number, Line, Article, Section, Annex

hierarchy_order = ['Anexo',
                   'Parte',
                   'Título',
                   'Capítulo',
                   'Secção',
                   'Sub-Secção',
                   'Artigo',
                   'Número',
                   'Alínea']

html_classes = {'Anexo': 'anexo',
                'Parte': 'parte',
                'Título': 'titulo',
                'Capítulo': 'capitulo',
                'Secção': 'seccao',
                'Sub-Secção': 'subseccao',
                'Artigo': 'artigo',
                'Número': 'numero list-unstyled',
                'Alínea': 'alinea list-unstyled'}

hierarchy_ids = {'Anexo': 'anexo',
                 'Parte': 'parte',
                 'Título': 'titulo',
                 'Capítulo': 'capitulo',
                 'Secção': 'seccao',
                 'Sub-Secção': 'subseccao',
                 'Artigo': 'artigo',
                 'Número': 'numero',
                 'Alínea': 'alinea'}


hierarchy_classes_with_titles = ['anexo', 'parte', 'titulo', 'capitulo',
                                 'seccao', 'subseccao', 'artigo']

hierarchy_html_titles = {'Parte': 'h2',
                         'Título': 'h3',
                         'Capítulo': 'h3',
                         'Secção': 'h4',
                         'Sub-Secção': 'h5',
                         'Anexo': 'h2',
                         'Artigo': 'h5'}

html_lists = {'Número': 'li', 'Alínea': 'li'}

formal_hierarchy_elements = ['Anexo', 'Artigo', 'Número', 'Alínea']


hierarchy_classes = {'Anexo': Annex,
                     'Parte': Section,
                     'Título': Section,
                     'Capítulo': Section,
                     'Secção': Section,
                     'Sub-Secção': Section,
                     'Artigo': Article,
                     'Número': Number,
                     'Alínea': Line,
                     }
