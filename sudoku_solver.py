# sudoku solver using csp (constraint satisfaction problem)


import time
import os

# get the folder where this script is located
# so we can find the puzzle files no matter where we run from
script_dir = os.path.dirname(os.path.abspath(__file__))

# step 1: reading and printing the board

def read_board(filename):
    board = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if len(line) == 9:  # only process lines with 9 digits
                row = []
                for ch in line:
                    row.append(int(ch))
                board.append(row)
    return board


def print_board(board):
    for i in range(9):
        if i % 3 == 0 and i != 0:
            print("------+-------+------")
        row_str = ""
        for j in range(9):
            if j % 3 == 0 and j != 0:
                row_str += "| "
            if board[i][j] == 0:
                row_str += ". "
            else:
                row_str += str(board[i][j]) + " "
        print(row_str)


# step 2: finding peers (cells that constrain each other)

def get_peers(row, col):
    peers = set()

    # cells in the same row
    for j in range(9):
        if j != col:
            peers.add((row, j))

    # cells in the same column
    for i in range(9):
        if i != row:
            peers.add((i, col))

    # cells in the same 3x3 box
    # find the top-left corner of the box
    box_row = (row // 3) * 3
    box_col = (col // 3) * 3
    for i in range(box_row, box_row + 3):
        for j in range(box_col, box_col + 3):
            if (i, j) != (row, col):
                peers.add((i, j))

    return peers


PEERS = {}
for r in range(9):
    for c in range(9):
        PEERS[(r, c)] = get_peers(r, c)


# step 3: setting up the csp

# create the initial domains for each cell

def setup_domains(board):
    domains = {}
    for i in range(9):
        for j in range(9):
            if board[i][j] != 0:
                # cell already filled, only one possible value
                domains[(i, j)] = set([board[i][j]])
            else:
                # empty cell, start with all values 1-9
                domains[(i, j)] = set([1, 2, 3, 4, 5, 6, 7, 8, 9])
    return domains


# step 4: ac-3 algorithm (arc consistency)

def revise(domains, xi, xj):
    revised = False
    values_to_remove = []

    for value in domains[xi]:
    
        has_support = False
        for other_value in domains[xj]:
            if other_value != value:
                has_support = True
                break

        if not has_support:
            # no valid value in xj for this value, so remove it from xi
            values_to_remove.append(value)
            revised = True

    # remove the unsupported values
    for v in values_to_remove:
        domains[xi].remove(v)

    return revised


# main ac-3 function

def ac3(domains):
    # build a queue of all arcs

    queue = []
    for cell in domains:
        for peer in PEERS[cell]:
            queue.append((cell, peer))

    # process arcs until queue is empty
    while len(queue) > 0:
        # take the first arc from the queue
        xi, xj = queue.pop(0)

        # try to revise xi's domain based on xj
        if revise(domains, xi, xj):
           
            if len(domains[xi]) == 0:
                return False

        
            for peer in PEERS[xi]:
                if peer != xj:
                    queue.append((peer, xi))

    # all arcs are consistent
    return True


# step 5: forward checking

def forward_check(domains, cell, value):
    # keep track of what we removed, so we can undo later
    removed = {}

    for peer in PEERS[cell]:
        if value in domains[peer]:
            # remove the value from peer's domain
            if peer not in removed:
                removed[peer] = set()
            removed[peer].add(value)
            domains[peer].remove(value)

            if len(domains[peer]) == 0:
                # undo everything we removed so far
                undo_forward_check(domains, removed)
                return None  # return none means failure

    return removed 


# undo the changes made by forward checking
def undo_forward_check(domains, removed):
    for peer in removed:
        for value in removed[peer]:
            domains[peer].add(value)


# step 6: backtracking search
def is_consistent(assignment, cell, value):
    for peer in PEERS[cell]:
        if peer in assignment and assignment[peer] == value:
            return False
    return True

def select_next_cell(domains, assignment):
    best_cell = None
    min_domain_size = 10  # bigger than any possible domain

    for cell in domains:
        if cell not in assignment:
            size = len(domains[cell])
            if size < min_domain_size:
                min_domain_size = size
                best_cell = cell

    return best_cell


# the main backtracking search function

def backtrack(domains, assignment):
    
    if len(assignment) == 81:
        return True
    cell = select_next_cell(domains, assignment)
    if cell is None:
        return False

    # try each value in the cell's domain
    # we make a sorted list so the order is deterministic
    for value in sorted(domains[cell]):

        # check if this value doesn't conflict with any peer
        if is_consistent(assignment, cell, value):

            # assign the value to this cell
            assignment[cell] = value
            old_domain = domains[cell].copy()  # save old domain
            domains[cell] = set([value])  # domain becomes just this value

            # forward check: remove this value from all peers' domains
            removed = forward_check(domains, cell, value)

            if removed is not None:
                # forward check succeeded, keep searching
                if backtrack(domains, assignment):
                    return True  # solution found!

                # undo the forward checking
                undo_forward_check(domains, removed)

            # undo the assignment (backtrack)
            del assignment[cell]
            domains[cell] = old_domain  # restore old domain

    # none of the values worked for this cell
    return False


# step 7: main solver that ties everything together

def solve(filename):
    print("=" * 50)
    print("solving:", filename)
    print("=" * 50)

    # step a: read the board from file
    board = read_board(filename)
    print("\ninput board:")
    print_board(board)

    # step b: setup the csp by creating domains for each cell
    domains = setup_domains(board)

    # count how many cells are empty
    empty_cells = 0
    for i in range(9):
        for j in range(9):
            if board[i][j] == 0:
                empty_cells += 1
    print("\nempty cells to fill:", empty_cells)

    # step c: run ac-3 to reduce domains before searching
    print("running ac-3 (arc consistency)...")
    ac3_result = ac3(domains)

    if not ac3_result:
        print("ac-3 found that this puzzle has no solution!")
        return

    # count how many cells ac-3 solved by itself
    solved_by_ac3 = 0
    for cell in domains:
        if len(domains[cell]) == 1 and board[cell[0]][cell[1]] == 0:
            solved_by_ac3 += 1
    print("cells solved by ac-3 alone:", solved_by_ac3)

    # step d: create initial assignment from filled cells and ac-3 results
    assignment = {}
    for cell in domains:
        if len(domains[cell]) == 1:
            # this cell has only one possible value
            assignment[cell] = list(domains[cell])[0]

    remaining = 81 - len(assignment)
    print("cells remaining for backtracking:", remaining)

    # step e: run backtracking search with forward checking
    if remaining > 0:
        print("running backtracking with forward checking...")
        start_time = time.time()
        result = backtrack(domains, assignment)
        end_time = time.time()

        if not result:
            print("no solution found!")
            return

        print("backtracking time: {:.4f} seconds".format(end_time - start_time))
    else:
        print("ac-3 solved the entire puzzle! no backtracking needed.")

    # step f: build and print the solved board
    solved_board = []
    for i in range(9):
        row = []
        for j in range(9):
            row.append(assignment[(i, j)])
        solved_board.append(row)

    print("\nsolved board:")
    print_board(solved_board)

    # step g: verify the solution is correct
    if verify_solution(solved_board):
        print("\nsolution is valid!")
    else:
        print("\nwarning: solution has errors!")

    print()


# step 8: verify that a solved board is correct

def verify_solution(board):
    # check each row has all digits 1-9
    for i in range(9):
        if set(board[i]) != set(range(1, 10)):
            print("row", i, "is invalid:", board[i])
            return False

    # check each column has all digits 1-9
    for j in range(9):
        col = []
        for i in range(9):
            col.append(board[i][j])
        if set(col) != set(range(1, 10)):
            print("column", j, "is invalid:", col)
            return False

    # check each 3x3 box has all digits 1-9
    for box_row in range(0, 9, 3):
        for box_col in range(0, 9, 3):
            box = []
            for i in range(box_row, box_row + 3):
                for j in range(box_col, box_col + 3):
                    box.append(board[i][j])
            if set(box) != set(range(1, 10)):
                print("box at ({},{}) is invalid:".format(box_row, box_col), box)
                return False

    return True


if __name__ == "__main__":

    files = ["easy.txt", "medium.txt", "hard.txt", "veryhard.txt"]

    for filename in files:

        filepath = os.path.join(script_dir, filename)

        # check if the file exists before trying to solve
        if os.path.exists(filepath):
            start = time.time()
            solve(filepath)
            end = time.time()
            print("total time for {}: {:.4f} seconds".format(filename, end - start))
            print()
        else:
            print("file '{}' not found, skipping...\n".format(filename))
