# -*- coding: utf-8 -*-

from formulas import register_formula
from formulas.expressions.base_expression import FBaseExpression
from formulas.expressions.predicates.base_predicate import FBasePredicate


@register_formula('like_predicate')
class FLikePredicate(FBasePredicate):
    def __init__(self, attr: FBaseExpression, prefix: str, suffix: str, no_pattern: bool = False):
        super(FLikePredicate, self).__init__(
            operator=None,
            operands=[attr, prefix, suffix, no_pattern],
        )

    def __str__(self):
        if self.operands[-1]:
            return f'LIKE_{self.operands[0]}'
        else:
            return f'LIKE_{self.operands[0]}%{self.operands[1]}'
