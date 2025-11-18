# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.predicates.base_predicate import FBasePredicate
from constants import VARCHAR


@register_formula('contain_predicate')
class FContainPredicate(FBasePredicate):
    def __init__(self, expression: FBaseExpression, substring):
        super(FContainPredicate, self).__init__(
            operator=None,
            operands=[expression, substring],
            type=VARCHAR,
        )

    def __str__(self):
        return f'CONTAIN_{self.operands[0]}_{self.operands[-1]}'
