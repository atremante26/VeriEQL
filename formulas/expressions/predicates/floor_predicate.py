# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.predicates.base_predicate import FBasePredicate


@register_formula('floor_predicate')
class FFloorPredicate(FBasePredicate):
    def __init__(self, expression: FBaseExpression):
        super(FFloorPredicate, self).__init__(
            operator=None,
            operands=[expression],
        )

    def __str__(self):
        return f'FLOOR_{self.operands[0]}'
