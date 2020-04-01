from .cell import Cell

class Row:

    def __init__(self, row_tag):
        self.row_tag = row_tag
        self.cells = self.add_cells()


    def add_cells(self):
        cells = []
        for cell_tag in self.row_tag.find_all('td'):
            cells.append(Cell(cell_tag))
        return cells


    def __repr__(self):
        result_list = ['\nrow:']
        for cell in self.cells:
            result_list.append(str(cell))
        return '\n'.join(result_list)
