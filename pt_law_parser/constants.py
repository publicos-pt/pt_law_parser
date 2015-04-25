hierarchy_priority = ['Anexo',
                      'Parte',
                      'Título',
                      'Capítulo',
                      'Secção',
                      'Sub-Secção',
                      'Artigo',
                      'Número',
                      'Alínea']

hierarchy_classes = {'Anexo': 'anexo',
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

hierarchy_html_lists = {'Número': 'li', 'Alínea': 'li'}

hierarchy_regex = {'Anexo': '^Anexo(.*)',
                   'Parte': '^Parte(.*)',
                   'Título': '^Título(.*)',
                   'Capítulo': '^Capítulo (.*)',
                   'Secção': '^Secção (.*)',
                   'Sub-Secção': '^SUBSecção (.*)',
                   'Artigo': '^Artigo (.*)$',
                   'Número': '^(\d+) - .*',
                   'Alínea': '^(\w+)\) .*',
                   }

formal_hierarchy_elements = ['Anexo', 'Artigo', 'Número', 'Alínea']
