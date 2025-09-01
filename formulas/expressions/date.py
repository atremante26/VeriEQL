# -*- coding: utf-8 -*-

import operator
from constants import (
    IntVal, ToReal,
    Z3_FALSE, Z3_TRUE,
    ArithRef, Z3_100, Z3_10000,
    # DATE,
)
from formulas import register_formula
from formulas.expressions import FDigits
from formulas.base_formula import BaseFormula
from z3 import (BoolRef, IntNumRef, RatNumRef)


@register_formula('date')
class FDate(BaseFormula):
    def __init__(self, year: str, month: str, day: str):
        self.year = IntVal(str(year)) if isinstance(year, str | int) else year
        self.month = IntVal(str(month)) if isinstance(month, str | int) else month
        self.day = IntVal(str(day)) if isinstance(day, str | int) else day
        if self.year is None and self.year is None and self.year is None:
            raise NotImplementedError(f"Only support Date('YYYY-MM-dd').")
        # self.type=DATE

    def __int__(self):
        return self.year * Z3_10000 + self.month * Z3_100 + self.day

    def __float__(self):
        return ToReal(self.__int__())

    def _f(self, op, other):
        if isinstance(other, FDate):
            return op(self.__int__(), other.__int__())
        elif isinstance(other, str):
            if str.isdigit(other):
                # date('2000-01-01')='20000101'
                return op(self.__int__(), FDigits(int(other)))
            elif str.isdecimal(other):
                # date('2000-01-01')='20000101.0'
                return op(self.__float__(), FDigits(float(other)))
            else:  # string of floats
                # date('2000-01-01')='abc'
                raise NotImplementedError(f"Cannot compare Date with Strings of non-decimals {other}.")
        elif isinstance(other, FDigits):
            return op(self.__int__(), other)
        elif isinstance(other, bool | BoolRef):
            if op in {operator.__add__, operator.__sub__, operator.__mul__, operator.__truediv__,
                      operator.__truediv__, operator.__mod__}:
                return op(self.__int__(), other)
            elif op in {operator.__gt__, operator.__ge__}:
                # date('2000-01-01') = true -> true
                return Z3_TRUE
            else:
                return Z3_FALSE
        elif isinstance(other, ArithRef | IntNumRef | RatNumRef):
            return op(self.__int__(), other)
        else:
            raise NotImplementedError(f"{operator}({self}, {other})")

    def __eq__(self, other):
        return self._f(operator.__eq__, other)

    def __add__(self, other):
        return self._f(operator.__add__, other)

    def __sub__(self, other):
        return self._f(operator.__sub__, other)

    def __mul__(self, other):
        return self._f(operator.__mul__, other)

    def __truediv__(self, other):
        return self._f(operator.__truediv__, other)

    def __floordiv__(self, other):
        return self._f(operator.__floordiv__, other)

    def __and__(self, other):
        return self._f(operator.__and__, other)

    def __or__(self, other):
        return self._f(operator.__or__, other)

    def __neg__(self):
        return Z3_FALSE

    def __mod__(self, other):
        return self._f(operator.__mod__, other)

    def __gt__(self, other):
        return self._f(operator.__gt__, other)

    def __ge__(self, other):
        return self._f(operator.__ge__, other)

    def __lt__(self, other):
        return self._f(operator.__lt__, other)

    def __le__(self, other):
        return self._f(operator.__le__, other)

    def __ne__(self, other):
        return self._f(operator.__ne__, other)

    def __str__(self):
        return f'Date_{self.year}_{self.month}_{self.day}'

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return 3

    def __getitem__(self, index):
        if index == 0:
            return self.year
        elif index == 1:
            return self.month
        elif index == 2:
            return self.day
        else:
            raise NotImplementedError(f"Out of index: {index} < 3.")
