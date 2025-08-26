# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.predicates.base_predicate import FBasePredicate


@register_formula('substr_predicate')
class FSubstrPredicate(FBasePredicate):
    def __init__(self, expression: FBaseExpression, offset: FBaseExpression | int, shift: FBaseExpression | int):
        super(FSubstrPredicate, self).__init__(
            operator=None,
            operands=[expression, offset, shift],  # must be strings
        )

    def __str__(self):
        return f'SUBSTR_{self.operands}'
