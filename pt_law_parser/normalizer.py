import re


def normalize(text):

    text = ' '.join(text.split())

    # substitute <br/> by </p><p>
    text = text.replace("<br />", "<br/>")
    text = text.replace("<br/>", "</p><p>")
    text = text.replace("<br >", "<br>")
    text = text.replace("<br>", "</p><p>")
    text = text.replace("<?xml version=\"1.0\" encoding=\"UTF-8\"?>", "")
    text = text.replace("<span>", "")
    text = text.replace("</span>", "")

    # strip inside tags
    text = text.replace('<p> ', '<p>')
    text = text.replace(' </p>', '</p>')

    text = text.replace('ARTIGO', 'Artigo')
    text = text.replace('PARTE', 'Parte')
    text = text.replace('TÍTULO', 'Título')
    text = text.replace('CAPÍTULO', 'Capítulo')
    text = text.replace('SECÇÃO', 'Secção')
    text = text.replace('ANEXO', 'Anexo')

    # older documents use "Art." instead of "Artigo"; change it
    text = re.sub('Art\. (\d+)\.º (.*?)',
                  lambda m: "Artigo %s.º %s" % m.group(1, 2),
                  text)

    # older documents use "Artigo #.º - 1" instead of "Artigo #.º 1"; change it
    text = re.sub('Artigo (\d+)\.º - (.*?)',
                  lambda m: "Artigo %s.º %s" % m.group(1, 2),
                  text)

    # create <p>'s specifically for start of articles
    text = re.sub("<p>Artigo (\d+)\.º (.*?)</p>",
                  lambda m: "<p>Artigo %s.º</p><p>%s</p>" % m.group(1, 2),
                  text)

    # add blockquote to changes
    text = text.replace('» </p>', '»</p>')
    text = text.replace(r'<p> «', r'<p>«')

    text = re.sub("<p>«(.*?)»</p>",
                  lambda m: "<p>«</p><p>%s</p><p>»</p>" % m.group(1),
                  text, flags=re.MULTILINE)

    # normalize bullets to "# -" (substituting the ones using #.)
    text = re.sub(r"<p>(\d+)\.",
                  lambda m: "<p>%s -" % m.group(1),
                  text)

    text = text.replace('.º', 'º')

    # remove <p> and replace </p> by '\n' so we are working on pure text.
    text = text.replace('</p>', '\n')
    text = text.replace('<p>', '')

    return text
