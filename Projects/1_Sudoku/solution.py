
from utils import *


row_units = [cross(r, cols) for r in rows]
column_units = [cross(rows, c) for c in cols]
square_units = [cross(rs, cs) for rs in ('ABC','DEF','GHI') for cs in ('123','456','789')]
unitlist = row_units + column_units + square_units

major_diagonal_units = [r+c for r, c in zip(rows, cols)]
minor_diagonal_units = [r+c for r, c in zip(rows, reversed(cols))]
diagonal_units = [major_diagonal_units, minor_diagonal_units]
unitlist = unitlist + diagonal_units


# Must be called after all units (including diagonals) are added to the unitlist
units = extract_units(unitlist, boxes)
peers = extract_peers(units, boxes)


def naked_twins(values):
    """Eliminate values using the naked twins strategy.

    The naked twins strategy says that if you have two or more unallocated boxes
    in a unit and there are only two digits that can go in those two boxes, then
    those two digits can be eliminated from the possible assignments of all other
    boxes in the same unit.

    Parameters
    ----------
    values(dict)
        a dictionary of the form {'box_name': '123456789', ...}

    Returns
    -------
    dict
        The values dictionary with the naked twins eliminated from peers

    Notes
    -----
    Your solution can either process all pairs of naked twins from the input once,
    or it can continue processing pairs of naked twins until there are no such
    pairs remaining -- the project assistant test suite will accept either
    convention. However, it will not accept code that does not process all pairs
    of naked twins from the original input. (For example, if you start processing
    pairs of twins and eliminate another pair of twins before the second pair
    is processed then your code will fail the PA test suite.)

    The first convention is preferred for consistency with the other strategies,
    and because it is simpler (since the reduce_puzzle function already calls this
    strategy repeatedly).

    See Also
    --------
    Pseudocode for this algorithm on github:
    https://github.com/udacity/artificial-intelligence/blob/master/Projects/1_Sudoku/pseudocode.md
    """
    from itertools import groupby
    valueof = lambda x: values[x]
    # compute removals
    removals = defaultdict(set) # box -> set of digits to remove
    for unit in unitlist:
        # strip singles
        unit = [box for box in unit if len(values[box]) > 1]
        # group boxes in the unit (assuming here that all box values are sorted)
        for group_digits, g in groupby(sorted(unit, key = valueof), key = valueof):
            group = list(g)
            if len(group) == len(group_digits):
                # multiples detected
                outsiders = [box for box in unit if box not in group]
                for outsider in outsiders:
                    outsider_digits = values[outsider]
                    if any(digit in outsider_digits for digit in group_digits):
                        removals[outsider].update(group_digits)
    # apply removals
    for box, group_digits in removals.items():
        value = values[box]
        for digit in group_digits:
            value = value.replace(digit, '')
        values = assign_value(values, box, value)
    return values


def eliminate(values):
    """Apply the eliminate strategy to a Sudoku puzzle

    The eliminate strategy says that if a box has a value assigned, then none
    of the peers of that box can have the same value.

    Parameters
    ----------
    values(dict)
        a dictionary of the form {'box_name': '123456789', ...}

    Returns
    -------
    dict
        The values dictionary with the assigned values eliminated from peers
    """
    for box, val in values.items():
        if len(val) == 1:
            for peer in peers[box]:
                peer_digits = values[peer]
                if val in peer_digits:
                    values = assign_value(values, peer, peer_digits.replace(val, ''))
    return values


def only_choice(values):
    """Apply the only choice strategy to a Sudoku puzzle

    The only choice strategy says that if only one box in a unit allows a certain
    digit, then that box must be assigned that digit.

    Parameters
    ----------
    values(dict)
        a dictionary of the form {'box_name': '123456789', ...}

    Returns
    -------
    dict
        The values dictionary with all single-valued boxes assigned

    Notes
    -----
    You should be able to complete this function by copying your code from the classroom
    """
    from collections import Counter
    for unit in unitlist:
        counter = Counter()
        for box in unit:
            counter.update(values[box])
        for digit, _ in filter(lambda x: x[1]==1, counter.items()):
            for box in unit:
                if digit in values[box]:
                    values = assign_value(values, box, digit)
    return values


def reduce_puzzle(values):
    """Reduce a Sudoku puzzle by repeatedly applying all constraint strategies

    Parameters
    ----------
    values(dict)
        a dictionary of the form {'box_name': '123456789', ...}

    Returns
    -------
    dict or False
        The values dictionary after continued application of the constraint strategies
        no longer produces any changes, or False if the puzzle is unsolvable 
    """
    stalled = False
    while not stalled:
        # Check how many boxes have a determined value
        solved_values_before = len([box for box in values.keys() if len(values[box]) == 1])

        values = eliminate(values)
        values = only_choice(values)
        values = naked_twins(values)

        # Check how many boxes have a determined value, to compare
        solved_values_after = len([box for box in values.keys() if len(values[box]) == 1])
        # If no new values were added, stop the loop.
        stalled = solved_values_before == solved_values_after
        # Sanity check, return False if there is a box with zero available values:
        if len([box for box in values.keys() if len(values[box]) == 0]):
            return False
    return values


def search(values):
    """Apply depth first search to solve Sudoku puzzles in order to solve puzzles
    that cannot be solved by repeated reduction alone.

    Parameters
    ----------
    values(dict)
        a dictionary of the form {'box_name': '123456789', ...}

    Returns
    -------
    dict or False
        The values dictionary with all boxes assigned or False

    Notes
    -----
    You should be able to complete this function by copying your code from the classroom
    and extending it to call the naked twins strategy.
    """
    # First, reduce the puzzle using the previous function
    values = reduce_puzzle(values)
    if not values:
        return values
    # collect unsolved boxes
    unsolved_boxes = [(box, len(values[box])) for box in values.keys() if len(values[box]) > 1]
    if not unsolved_boxes:
        return values
    # pick unsolved box with fewer number of possibilities
    unsolved_box, _ =  min(unsolved_boxes, key=lambda x: x[1])
    # Now use recursion to solve each one of the resulting sudokus, and if one returns a value (not False), return that answer!
    for possible_value in values[unsolved_box]:
        possible_values = values.copy()
        possible_values[unsolved_box] = possible_value
        possible_values = search(possible_values)
        if possible_values:
            return possible_values
    return False


def solve(grid):
    """Find the solution to a Sudoku puzzle using search and constraint propagation

    Parameters
    ----------
    grid(string)
        a string representing a sudoku grid.
        
        Ex. '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'

    Returns
    -------
    dict or False
        The dictionary representation of the final sudoku grid or False if no solution exists.
    """
    values = grid2values(grid)
    values = search(values)
    return values


if __name__ == "__main__":
    diag_sudoku_grid = '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'
    display(grid2values(diag_sudoku_grid))
    result = solve(diag_sudoku_grid)
    display(result)

    try:
        import PySudoku
        PySudoku.play(grid2values(diag_sudoku_grid), result, history)

    except SystemExit:
        pass
    except:
        print('We could not visualize your board due to a pygame issue. Not a problem! It is not a requirement.')
