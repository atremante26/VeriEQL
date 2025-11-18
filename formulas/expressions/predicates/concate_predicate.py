# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.predicates.base_predicate import FBasePredicate
from constants import VARCHAR


@register_formula('concate_predicate')
class FConcatePredicate(FBasePredicate):
    def __init__(self, expression: FBaseExpression, *strings):
        super(FConcatePredicate, self).__init__(
            operator=None,
            operands=[expression, *strings],
            type=VARCHAR,
        )

    def __str__(self):
        return f'CONCATE_{"_".join(map(str, self.operands))}'
