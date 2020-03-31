from .cell import Cell

class Row():

    def __init__(self, row_tag):
        self.row_tag = row_tag
        self.cells = self.add_cells()
        self.update_start_stop_rows()
        self.update_start_stop_cols()


    def update_start_stop_rows(self):
        cur_row = 1
        for cell in self.cells:
            cur_row = cell.update_start_stop_rows(cur_row)


    def update_start_stop_cols(self):
        cur_col = 1
        for cell in self.cells:
            cur_col = cell.update_start_stop_cols(cur_col)


    def __iter__(self):
        self.cell_iter_pos = 0
        return self


    def __next__(self):
        if self.cell_iter_pos >= len(self.cells):
            raise StopIteration

        cell = self.cells[self.cell_iter_pos]
        self.cell_iter_pos += 1
        return cell


    def add_cells(self):
        cells = []
        for cell_tag in self.row_tag.find_all('td'):
            cells.append(Cell(cell_tag))
        return cells


    def __repr__(self):
        # result_list = ['row_tag: ' + str(self.row_tag)]
        result_list = ['\nrow:']
        for cell in self.cells:
            result_list.append(str(cell))
        return '\n'.join(result_list)
