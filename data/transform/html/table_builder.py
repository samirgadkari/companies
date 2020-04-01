

class TableBuilder():

    def __init__(self, filename):
        self.soup = BeautifulSoup(data(filename), 'html.parser')
        self.data = self.shorten()

    def shorten(self):
        self.add_style_attr_to_td()
        self.tags()
        self.attrs()
        return str(self.soup)

    def all_tags(self):
        return self.soup.find_all(True)

    def text(self):
        return self.soup.get_text()

    def attrs(self):
        tags = self.all_tags()
        for tag in tags:
            attributes = [attr for attr in tag.attrs.keys()]
            for attr in attributes:
                if attr not in ['rowspan', 'colspan', 'style']:
                    del tag[attr]

    def tags(self):
        table_tag_names = set(['table', 'th', 'tr', 'td'])
        all_tag_names = set(map(lambda t: t.name, self.all_tags()))
        remove_tag_names = all_tag_names.difference(table_tag_names)
        for tag_name in remove_tag_names:
            tags = self.soup.find_all(tag_name)
            for tag in tags:
                tag.unwrap() # keep the content, but remove the surrounding tag

    def add_style_attr_to_td(self):
        tds = self.soup('td')
        for td in tds:
            alignment = 'left'  # By default, text in tds are left-aligned
            elements = td.find_all(style=True)
            for e in elements:
                styles = e['style']
                matches = Html.text_align_attr.search(styles)
                if matches is not None:
                    alignment = matches.group(1)
            td['style'] = f'text-align:{alignment}'
