# -*- coding: utf-8 -*-


from z3 import (
    ArithRef,
    is_seq,
)
from constants import (
    And,
    Not,
    NumericType,
)
from errors import NotSupportedError


class FExpressionTuple:
    __slots__ = ['VALUE', 'NULL', 'attribute', 'tuple']

    def __init__(self, NULL=None, VALUE=None, attribute=None, tuple=None):
        # self.VALUE: IntermFunc | Callable | BaseFormula = None
        # self.NULL: IntermFunc | Callable | BaseFormula = None
        self.NULL = NULL
        self.VALUE = VALUE
        self.attribute = attribute
        self.tuple = tuple

    def __call__(self, *args, **kwargs):
        return self.VALUE(*args, **kwargs)

    def __str__(self):
        return f"{self.__class__.__name__}(NULL={self.NULL}, VALUE={self.VALUE})"

    def __eq__(self, other):
        from formulas.expressions.date import FDate

        if isinstance(other, FExpressionTuple):
            if (isinstance(self.VALUE, NumericType) and is_seq(other.VALUE)) or \
                    (is_seq(self.VALUE) and isinstance(other.VALUE, NumericType)):
                raise NotSupportedError(
                    "In the outermost projection, You compare a String with a numerical which is NOT allowed.")
            elif isinstance(self.VALUE, FDate) and isinstance(other.VALUE, FDate):
                # TODO: build a class like FDate to define implicit type conversion within it.
                return And(self.NULL == other.NULL, self.VALUE.year == other.VALUE.year,
                           self.VALUE.month == other.VALUE.month,
                           self.VALUE.day == other.VALUE.day)
            return And(self.NULL == other.NULL, self.VALUE == other.VALUE)
        elif isinstance(other, ArithRef):
            return And(Not(self.NULL), self.VALUE == other)
        else:
            raise NotImplementedError

    def __repr__(self):
        return self.__str__()
