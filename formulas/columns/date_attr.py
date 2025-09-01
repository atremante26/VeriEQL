# -*- coding:utf-8 -*-

from copy import copy

from typing import Callable

from constants import (
    NumericType,
    Z3_NULL_VALUE,
    Z3_FALSE,
    Z3_TRUE,
    DATE,
    ArithRef,
)
from .attribute import FAttribute
from formulas import register_formula
from formulas.expressions.expression_tuple import FExpressionTuple
from formulas.expressions.null import FNull
from formulas.expressions.date import FDate


@register_formula('date_attr')
class FDateAttribute(FAttribute):
    __slots__ = [
        # name
        'prefix', 'name',
        # z3
        'VALUE', 'NULL', '__STRING_SORT__',
        # alias expression
        'EXPR', 'EXPR_CALL', 'require_tuples', '_sugar_name', '_sugar_full_name',
        # day functions
        'year_func', 'month_func', 'day_func'
    ]

    def __init__(self,
                 scope,
                 literal: str,
                 prefix: str,
                 # map date to year/month/day
                 year_func: Callable = None, month_func: Callable = None, day_func: Callable = None,
                 type: str = DATE,
                 _uuid: int = None,
                 ):
        self.year_func = year_func
        self.month_func = month_func
        self.day_func = day_func
        super(FDateAttribute, self).__init__(scope, literal, prefix, type, _uuid)

    def detach(self):
        # deepcopy will copy `self.EXPR`
        attribute = copy(self)
        attribute.EXPR = None
        attribute.require_tuples = False
        attribute._sugar_full_name = attribute._sugar_name = None
        attribute.uninterpreted_func = None
        return attribute

    def update_alias(self, scope, alias_prefix, alias_name, **kwargs):
        attr = self.detach()
        attr.prefix = alias_prefix
        attr.name = alias_name
        attr._sugar_full_name = self.__str__()
        attr._sugar_name = self.name
        attr.uninterpreted_func = self.uninterpreted_func
        return attr

    def __eq__(self, other):
        from visitors.interm_function import IntermFunc
        if isinstance(other, FDateAttribute):
            return hash(self) == hash(other) and self.VALUE == other.VALUE
        elif isinstance(other, IntermFunc):
            return self in other.attributes
        elif isinstance(other, str):
            return other == self.name or self.__str__() == other or \
                self._sugar_name is not None and self._sugar_name == other or \
                self._sugar_full_name is not None and self._sugar_full_name == other
        else:
            return False

    def __hash__(self):
        return self._uuid

    def __call__(self, *args, **kwargs):
        return FExpressionTuple(self.NULL(*args, **kwargs), self.VALUE(*args, **kwargs))

    def __expr__(self, src_tuples, **kwargs):
        from formulas.columns.aggregations import AggregationType
        from formulas.expressions.expression import FExpression
        from formulas.expressions.predicates.case_predicate import FCasePredicate
        from formulas.expressions.predicates.last_value_predicate import FLastValuePredicate
        from formulas.expressions.digits import FDigits

        if isinstance(self.EXPR, FLastValuePredicate):
            # pass
            raise NotImplementedError
        elif not self.require_tuples and isinstance(src_tuples, list):
            # src_tuples = src_tuples[0]
            raise NotImplementedError

        if isinstance(self.EXPR, AggregationType):  # Aggregation
            # return self.EXPR.__expr__(src_tuples, **kwargs)
            raise NotImplementedError
        elif isinstance(self.EXPR, FCasePredicate | FExpression):
            # return self.EXPR_CALL(src_tuples, **kwargs)
            raise NotImplementedError
        elif isinstance(self.EXPR, FNull):
            # return FExpressionTuple(Z3_TRUE, Z3_NULL_VALUE)
            raise NotImplementedError
        elif isinstance(self.EXPR, FDigits):
            # return FExpressionTuple(Z3_FALSE, self.EXPR_CALL(None))
            raise NotImplementedError
        elif isinstance(self.EXPR, NumericType | ArithRef):
            # return FExpressionTuple(Z3_FALSE, self.EXPR)
            raise NotImplementedError
        elif self.EXPR is None:  # FSymbol
            # return FExpressionTuple(Z3_FALSE, self.VALUE(None))
            raise NotImplementedError
        else:
            raise NotImplementedError(self.EXPR)
