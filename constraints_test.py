from verieql import verify_sql_equivalence
from constraint_extraction.extract_constraints import extract
from constants import DIALECT
import os

def test_constraint(db_path):
    schema, constraints_dict = extract(db_path) 
    
    db_name = os.path.basename(db_path)
    
    # Extract constraints for specific DB
    constraints = constraints_dict[db_name][0]
    
    sql1 = "SELECT * FROM EXAMINATION"
    sql2 = "SELECT * FROM EXAMINATION WHERE ID IS NOT NULL"
    
    config = {
        'generate_code': True,
        'timer': True,
        'show_counterexample': True,
        'dialect': DIALECT.MYSQL,
        'all_null_is_deleted': False,
    }
    
    result = verify_sql_equivalence(
        sql1, 
        sql2, 
        schema,
        ROW_NUM=2, 
        constraints=constraints,
        **config
    )
    
    print(f"\n{'='*60}")
    print(f"Equivalent: {result['equivalent']}")
    print(f"Time cost: {result['time_cost']}")
    if result['counterexample']:
        print(f"\nCounterexample:\n{result['counterexample']}")
    print(f"{'='*60}\n")
    
    return result

if __name__ == '__main__':
    result = test_constraint('constraint_extraction/thrombosis_prediction')


'''
Not Null: Existed but bug
- Initial call to _f(constraint) in environment.py -> constraint = {'not_null': [{'value': 'EMPLOYEES__ID'}]}
- Matches isinstance(constraint, dict) -> goes to 'not_null' case
    - operator = 'not_null'
    - operands = [{'value': 'EMLOYEES__ID'}]
    - Second call to _f(operands)
- Matches isinstance(operands, list) -> iteratives over list and calls [_f(e) for e in expr (operands)]
- Matches isinstance(e, dict) -> goes to 'value' case ({'value': 'EMLOYEES__ID'})
    - operator = 'value'
    - operands = 'EMPLOYEES__ID'
    - Calls _get_attribute(operands) -> returns list of FExpressionTuples
- Recursion carries back to original 'not_null' case (operands = _f(operands))
    - operands = [[FExpressionTuple(...), FExpressionTuple(...)]] (nested list because of wrapping in [_f(e) for e in expr] step)
- return And(*[Not(opd.NULL) for opd in operands])
    - Caused error because each opd is a list and opd.NULL tries to apply NULL attribute to list

Solution: Iterate manually and unpack nested list
    - Iterate over elements in operands (which is currently the list: [{'value': 'EMLOYEES__ID'}])
    - Each element is a dict, so we call attr = _f(opd) on this dict element
    - This returns only a single list of FExpressionTuples: attrs = [FExpressionTuple(...), FExpressionTuple(...)]
    - Apply not null constraint to each tuple in list
    - Return conjunction of constraints

NOTE: Primary keys already have not null constraint applied

Use 'between' constraint for ranges?
Use 'in' constraint for categorical?
'''