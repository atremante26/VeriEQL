# -*- coding:utf-8 -*-

from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.predicates.base_predicate import FBasePredicate
from constants import DATE


@register_formula('to_int_predicate')
class FToIntPredicate(FBasePredicate):
    def __init__(self, expression: FBaseExpression):
        super(FToIntPredicate, self).__init__(
            operator=None,
            operands=[expression],
        )

    def __str__(self):
        return f'INT_{self.operands[0]}'
