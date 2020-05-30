import re
import pdfkit
from bs4 import BeautifulSoup
from pdf2image import convert_from_path


def remove_escaped_strings(raw_html):
    escaped_str_regex = re.compile(r'&#\d+;')
    return escaped_str_regex.sub('', raw_html)


def remove_superscripts(table_tag):
    sups = table_tag.find_all('sup')
    for sup in sups:
        sup.decompose()
    return table_tag


def html_to_image(filename):
    with open(filename, 'r') as f:

        raw_html = f.read()
        clean_html = remove_escaped_strings(raw_html)

        table_tag = BeautifulSoup(clean_html, 'html.parser')
        table_tag = remove_superscripts(table_tag)

        # Change the table style to:
        style = "font-family:Lucida Console;font-size:96pt;margin-left:auto;" \
            "margin-right:auto;width:100%;border:collapse;text-align:left;"
        table_tag['style'] = style

        # Specify a large page size, so our PDF is huge.
        # A large PDF is required for
        # better OCR (Optical Character Recognition)
        pdfkit.from_string(str(table_tag),
                           'out.pdf',
                           options={'page-size': 'A2'})

        images = convert_from_path('out.pdf')
        # import pdb; pdb.set_trace()
        images[0].save('out.png', 'PNG')


if __name__ == "__main__":
    html_to_image('./data/extract/samples/html/html_input/1.html')
