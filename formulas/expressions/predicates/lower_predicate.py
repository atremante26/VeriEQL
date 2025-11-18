# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.predicates.base_predicate import FBasePredicate
from constants import VARCHAR


@register_formula('lower_predicate')
class FLowerPredicate(FBasePredicate):
    def __init__(self, expression: FBaseExpression):
        super(FLowerPredicate, self).__init__(
            operator=None,
            operands=[expression],
            type=VARCHAR,
        )

    def __str__(self):
        return f'LOWER_{self.operands[0]}'
