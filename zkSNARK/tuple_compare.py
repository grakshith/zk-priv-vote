import sys

from pysnark.runtime import PrivVal, PubVal, snark
from pysnark.branching import BranchingValues, if_then_else, _if, _elif, _else, _endif, _range, _while, _endwhile, _endfor, _breakif


@snark
def tuple_compare(x, y):
    _ = BranchingValues()
    r1 = (x[0] == y[0])
    r2 = (x[1] == y[1])
    if _if(r1):
        if _if(r2):
            _.x = 0
        if _else():
            _.x = 1
        _endif()
    if _else():
        _.x = 1
    _endif()

    return _.x



print(tuple_compare((1,3), (1,2)))
