'''
Convert the HTML file that contains a single table tag
into a large PNG file with large font sizes.
The size required is large since
OCR (Optical Character Recognition) is easier with
larger font sizes. The large file size gives ample
space between word groups.
'''
import re
import pdfkit
from bs4 import BeautifulSoup
from pdf2image import convert_from_path


def remove_escaped_strings(raw_html):
    '''
    Remove escaped strings.
    They don't contain any information we need.
    '''
    escaped_str_regex = re.compile(r'&#\d+;')
    return escaped_str_regex.sub('', raw_html)


def remove_superscripts(table_tag):
    '''
    Remove superscripts.
    They don't contain any information we need,
    and are not easy to do OCR with.
    '''
    sups = table_tag.find_all('sup')
    for sup in sups:
        sup.decompose()
    return table_tag


def html_to_image(filename):
    '''
    Convert the given HTML file into a PNG file.
    '''
    with open(filename, 'r') as f:

        raw_html = f.read()
        clean_html = remove_escaped_strings(raw_html)

        table_tag = BeautifulSoup(clean_html, 'html.parser')
        table_tag = remove_superscripts(table_tag)

        # Change the table style to the one given below.
        # This style is good for OCR (Optical Character Recognition)
        # which we will do after generating the image.
        style = "font-family:Lucida Console;font-size:96pt;margin-left:auto;" \
            "margin-right:auto;width:100%;border:collapse;text-align:left;"
        table_tag['style'] = style

        # Convert the html tag into pdf.
        # Specify a large page size, so our PDF is huge.
        # A large PDF is required for
        # better OCR (Optical Character Recognition)
        pdfkit.from_string(str(table_tag),
                           'out.pdf',
                           options={'page-size': 'A2'})

        # Save the pdf file as a png file.
        images = convert_from_path('out.pdf')
        images[0].save('out.png', 'PNG')


if __name__ == "__main__":
    html_to_image('./data/extract/samples/html/html_input/1.html')
