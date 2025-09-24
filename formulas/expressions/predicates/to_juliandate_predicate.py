# -*- coding:utf-8 -*-

from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.predicates.base_predicate import FBasePredicate
from constants import DATE


@register_formula('to_juliandate_predicate')
class FToJulianDatePredicate(FBasePredicate):
    def __init__(self, expression: FBaseExpression):
        super(FToJulianDatePredicate, self).__init__(
            operator=None,
            operands=[expression],
            type=DATE,
        )

    def __str__(self):
        return f'JULIANDATE_{self.operands[0]}'
