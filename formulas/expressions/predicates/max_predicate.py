# -*- coding: utf-8 -*-

from typing import List
from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.predicates.base_predicate import FBasePredicate


@register_formula('max_predicate')
class FMaxPredicate(FBasePredicate):
    def __init__(self, operands: List[FBaseExpression]):
        super(FMaxPredicate, self).__init__(
            operator=None,
            operands=operands,
        )

    def __str__(self):
        return f'MAX_{"_".join([opd for opd in self.operands])}'
