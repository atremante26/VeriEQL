# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.expressions.uniter_functions.base_function import FUninterpretedFunction


@register_formula('udate')
class FUDate(FUninterpretedFunction):
    def __init__(self, value):
        self.EXPR = value
        super(FUDate, self).__init__(operands=['UDATE', self.EXPR])
