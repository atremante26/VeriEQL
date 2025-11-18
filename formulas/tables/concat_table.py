# -*- coding:utf-8 -*-

from typing import Sequence

from formulas import register_formula
from formulas.tables.base_table import FBaseTable
from formulas.tuples.inner_join_tuple import FInnerJoinTuple


def _projection(
        scope,
        tables: Sequence[FBaseTable],
        name: str,
):
    tuple_list = [table[0] for table in tables]
    tuple = FInnerJoinTuple(*tuple_list, condition=None, name=scope._get_new_tuple_name())
    scope.register_tuple(tuple.name, tuple)
    tuple.SORT = scope._declare_tuple_sort(tuple.name)
    return tables, [tuple]


@register_formula('concat_table')
class FConcatTable(FBaseTable):
    def __init__(self,
                 scope,
                 tables: Sequence[FBaseTable],
                 # condition: Sequence[str],
                 name: str = None,
                 ):
        # concatenate tables' columns, only consider the 1st tuple
        name = name or scope._get_new_databases_name()
        prev_tables, curr_table = _projection(scope, tables, name)
        super(FConcatTable, self).__init__(curr_table, name)
        scope.register_database(name, self)
        self.fathers = tables
        self.root = [t.root for t in tables]

    @property
    def condition(self):
        return None
