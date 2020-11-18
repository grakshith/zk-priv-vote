import sys

from pysnark.runtime import PrivVal, PubVal, snark
from pysnark.branching import BranchingValues, if_then_else, _if, _elif, _else, _endif, _range, _while, _endwhile, _endfor, _breakif



def tuple_compare(x, y):
    _ = BranchingValues()
    r1 = (x[0] == y[0])
    r2 = (x[1] == y[1])
    r3 = (x[0] == y[1])
    r4 = (x[1] == y[0])
    if _if(r1):
        if _if(r2):
            _.x = 1
        if _else():
            _.x = 0
        _endif()
    if _else():
        _.x = 0
    _endif()

    if _if(r3):
        if _if(r4):
            _.y = 1
        if _else():
            _.y = 0
        _endif()
    if _else():
        _.y = 0
    _endif()

    _.z = 0
    if _if(_.x):
        _.z = _.x
    _endif()
    if _if(_.y):
        _.z = _.y
    _endif()

    return _.z


if __name__ == "__main__":
    print(tuple_compare((2,1), (1,2)))
