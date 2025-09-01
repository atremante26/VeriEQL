# -*- coding:utf-8 -*-

from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.predicates.base_predicate import FBasePredicate
from constants import DATE


@register_formula('to_date_predicate')
class FToDatePredicate(FBasePredicate):
    def __init__(self, expression: FBaseExpression):
        super(FToDatePredicate, self).__init__(
            operator=None,
            operands=[expression],
            type=DATE,
        )

    def __str__(self):
        return f'DATE_{self.operands[0]}'
