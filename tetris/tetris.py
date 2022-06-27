"""
Author: eds89
Date: 31/05/2022
"""
import sys
import numpy as np


class Piece(object):
    """
    Class to hold information about Pieces.
    """
    def __init__(self, name, block: np.array, invisible_points=[]):
        self.name = name
        self.block = block
        self.height = block.shape[0]
        self.width = block.shape[1]
        self.shape = block.shape
        # multi-indices of invisible points in the piece's block
        self.invisible_points = invisible_points

    def __repr__(self):
        block_str = str(self.block).replace("\n", "\n   ")
        return f"{self.name}: {block_str} {self.shape}"
        # return "{0}:{1}({2})".format(self.name, self.block,
        #                           self.dim)


PieceQ = Piece("Q", np.array([[1, 1],
                              [1, 1]]))
PieceS = Piece("S", np.array([[0, 1, 1],
                              [1, 1, 0]]),
               invisible_points=[(0, 0), (1, 2)])
PieceZ = Piece("Z", np.array([[1, 1, 0],
                              [0, 1, 1]]),
               invisible_points=[(0, 2), (1, 0)])
PieceJ = Piece("J", np.array([[0, 1],
                              [0, 1],
                              [1, 1]]),
               invisible_points=[(0, 0), (1, 0)])
PieceL = Piece("L", np.array([[1, 0],
                              [1, 0],
                              [1, 1]]),
               invisible_points=[(0, 1), (1, 1)])
PieceI = Piece("I", np.array([[1, 1, 1, 1]]))

PieceT = Piece("T", np.array([[1, 1, 1],
                              [0, 1, 0]]),
               invisible_points=[(1, 0), (1, 2)])

available_pieces = {
    "Q": PieceQ,
    "S": PieceS,
    "Z": PieceZ,
    "J": PieceJ,
    "L": PieceL,
    "I": PieceI,
    "T": PieceT
}
#for k, v in available_pieces.items():
#    print(f"({k} : {v})")

START_GRID_HEIGHT = 5
EXPANSION_TRIGGER = 3
EXPANSION_GRID_HEIGHT_INCREMENTS = 3
DEFAULT_GRID_WIDTH = 10

GRID = np.zeros(shape=(START_GRID_HEIGHT, DEFAULT_GRID_WIDTH))

def reset_grid():
    """
    Resets GRID to zero.
    :return:
    """
    global GRID
    GRID = np.zeros(shape=(START_GRID_HEIGHT, DEFAULT_GRID_WIDTH))


def expand_grid_upward(number_rows=EXPANSION_GRID_HEIGHT_INCREMENTS):
    """
    Expand GRID upward to make room for more pieces.
    :param number_rows:
    :return:
    """
    global GRID
    extra_rows = np.zeros(shape=(number_rows, DEFAULT_GRID_WIDTH))
    GRID = np.append(extra_rows, GRID, axis=0)


def delete_filled_rows():
    """
    Delete all rows filled with 1.
    :return:
    """
    global GRID
    ## removes filled rows:
    filled_row_indices = [idx for idx, i in enumerate(np.logical_and.reduce(GRID, axis=1)) if i]
    print("filled_row_indices", filled_row_indices)
    if len(filled_row_indices) > 0:  # there are filled rows
        GRID = np.delete(GRID, filled_row_indices, axis=0)

    # returns the number of filled rows
    return len(filled_row_indices)




def find_highest_row_index(selected_cols: np.array):
    """
    Finds the index of the highest occupied column for a particular area.
    :param selected_cols:
    :return:
    """
    print("find_highest_row_index()")
    reduced = np.logical_or.reduce(selected_cols, axis=1)
    print("\tlogical_or reduced:", reduced)
    highest_index = len(selected_cols) - 1  # or -1
    print("\tpre highest_index:", highest_index)
    for idx, i in enumerate(reduced):
        if i:
            highest_index = idx
            break
    print("\tfinal highest_index", highest_index)
    return highest_index


def calculate_start_end_rows(piece: Piece, col_area: np.array):
    """
    Calculate start and end rows for a new piece taking into account existing pieces around same index.
    :param piece:
    :param col_area:
    :return:
    """
    # Calculates the highest column from the column range where the piece will fall at.
    # Remind the piece widths are fixed.
    highest_row = find_highest_row_index(col_area)

    # checks whether the highest row and the bottom-most row.
    # If so, calculates the start_row index accordingly
    if highest_row == len(col_area) - 1:
        start_row = len(col_area) - piece.height
    # checks whether there are any invisible points at line 1 of a piece,
    # if so, adds 1 to start_row to accommodate for this. This is useful to
    # make sure pieces with blank dots (e.g. T, Z and S) will 'lock' correctly on
    # the block immediately below it.
    # This routine can eventually result in a collision, which is dealt with further below.
    else:
        # has_invisible_row_1 = False
        # for e in l:
        # if e[0] == 1:
        # has_invisible_row_1 = True
        # break
        start_adjust_inv_points = 1 if len(piece.invisible_points) > 0 else 0
        start_row = highest_row - piece.height + start_adjust_inv_points
    end_row = start_row + piece.height

    # print(col_area[start_row:end_row,:])
    # print(type(col_area[start_row:end_row,:]))
    # print(piece)
    # print(type(piece))
    # print("begin start-end", start_row, end_row)
    has_collisions = check_collision(piece, col_area[start_row:end_row, :])
    # print(has_collisions)

    # if a collision is found, then moves start and end row indices one position upward
    if has_collisions:  # a collision has happened
        start_row -= 1
        end_row -= 1
    # print("final start-end", start_row, end_row)
    # start and end rows are returned as a tuple
    return start_row, end_row


def check_collision(piece: Piece, area: np.array):
    """
    Check whether a piece collides with an existing piece.
    :param piece:
    :param area:
    :return:
    """
    # Performs a logical AND operation to determine whether any block of piece
    # collides with the area. A collision is represented by 1 occupying the same
    # coordinates in the piece block and area.
    collisions_el = np.logical_and(area, piece.block)
    # print(collisions_el)

    # Uses a logical OR to propagate any element collisions until obtainig a single
    # boolean value indicating whether an element collided wherever in the area.
    # True OR anything always results in True, hence whatever collision is propagated further down
    collisions_per_rows = np.logical_or.reduce(collisions_el, axis=1)
    # Last logical OR to get the final collision state
    collisions_final = np.logical_or.reduce(collisions_per_rows, axis=0)

    return collisions_final


def copy_into_grid(piece: Piece, area: np.array):
    """
    Copy a piece into the area. Both must have same shape.
    :param piece:
    :param area:
    :return:
    """
    # initializes a context manager to write the piece block on the corresponding area
    # the 'multi_index' flag helps to account for invisible points in the block and ignore these while
    # copying the piece block into the array
    # The `writeonly` op_flags broadcasts changes to the main GRID matrix
    with np.nditer(area, flags=["multi_index"], op_flags=["writeonly"]) as it:
        for x in it:
            curr_index = it.multi_index
            # if the current index is an invisible point, then ignore it.
            # This prevents the 0's from a piece's block being copied over existing pieces.
            if curr_index in piece.invisible_points:
                continue
            x[...] = piece.block[curr_index]
            # print(x, curr_index)


def drop_piece(piece: Piece, index=0):
    """
    Drops a piece at `index`. The challenge is to calculate the start_row index correctly, taking into account that
    some pieces have invisible blocks.
    This function uses sub-functions defined above.
    :param piece:
    :param index:
    :return:
    """
    if index + piece.width - 1 >= DEFAULT_GRID_WIDTH:
        raise ValueError("Piece {} does not fit at index {}".format(
            piece.name, index))
    start_col = index
    end_col = index + piece.width

    start_row, end_row = calculate_start_end_rows(piece, GRID[:, start_col:end_col])
    # start_row = find_highest_row_index() - 1
    # print(f"{start_row}, {end_row}")
    # start_row = GRID.shape[0] - piece.height
    # end_row = start_row + piece.height

    grid_area = GRID[start_row:end_row, start_col:end_col]

    copy_into_grid(piece, grid_area)


def process(input_sequence: str):
    """
    The main logic. Processes each move (piece+index) in the sequence given.
    :param input_sequence:
    :return: the final height of blocks in the grid.
    """
    # clears grid for each sequence (input line
    reset_grid()
    height = 0
    for idx, move in enumerate(input_sequence.split(",")):
        print(f"======== begin move {idx} ========")
        curr_piece = available_pieces[move[0]]
        curr_index = int(move[1])

        print("Dropping piece {0} at index {1}".format(
            curr_piece.name, curr_index))
        drop_piece(curr_piece, curr_index)

        # checks and deletes filled rows
        deleted_indices_count = delete_filled_rows()

        print("Deleted row indices {0}".format(deleted_indices_count))
        if deleted_indices_count > 0:
            expand_grid_upward(deleted_indices_count)

        print("highest_row_grid")
        highest_row_grid = find_highest_row_index(GRID)
        print("\thighest_row_grid:", highest_row_grid)
        if highest_row_grid == len(GRID) - 1 and np.count_nonzero(GRID[-1, :]) == 0:
            # GRID[-1,:] == 0: #np.zeros(shape=(1,DEFAULT_GRID_WIDTH)):
            height = 0
        else:
            height = len(GRID) - highest_row_grid

        # normalizes the highest_row_grid count
        # norm_highest_row_grid = len(GRID) - (highest_row_grid + 1) if len(GRID) == (highest_row_grid+1) else len(GRID) - highest_row_grid
        # print("column height is", norm_highest_row_grid)
        if highest_row_grid <= EXPANSION_TRIGGER:
            expand_grid_upward()

        print(f"After move {idx + 1}, the grid is: ")
        print(GRID)
        print(f"Height is {height}")
        print(f"======== end move {idx} ========")
    return height


def main():
    """
    The main method. Reads the input file and saves output result to file.
    :return:
    """
    print("main()")
    args = sys.argv[1:]
    print(args)
    if len(args) != 2:
        raise ValueError("both input_file and output_file must be provided.")
    input_file = args[0]
    output_file = args[1]
    results = []
    with open(input_file, "r") as fr:
        for line in fr:
            #line = fr.readline()
            print("Input line:", line)
            result = process(line)
            print("Result:", result)
            results.append(result)
    print(results)
    with open(output_file, "w") as fp:
        print("Writing result to {}".format(output_file))
        for result in results:
            fp.write(str(result))
            fp.write("\n")

if __name__ == "__main__":
    main()
