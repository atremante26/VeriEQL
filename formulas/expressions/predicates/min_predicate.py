# -*- coding: utf-8 -*-

from typing import List
from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.predicates.base_predicate import FBasePredicate


@register_formula('min_predicate')
class FMinPredicate(FBasePredicate):
    def __init__(self, operands: List[FBaseExpression]):
        super(FMinPredicate, self).__init__(
            operator=None,
            operands=operands,
        )

    def __str__(self):
        return f'MIN_{"_".join([str(opd) for opd in self.operands])}'
