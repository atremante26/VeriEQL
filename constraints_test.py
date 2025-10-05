from verieql import verify_sql_equivalence
from constants import DIALECT

def test_constraint():
    
    # Define a minimal schema
    schema = {
        'EMPLOYEES': {
            'ID': 'INTEGER',
            'NAME': 'VARCHAR',
            'SALARY': 'INTEGER',
            'DEPARTMENT': 'VARCHAR',
            'AGE': 'INTEGER'
        }
    }
    
    # Define constraints
    #constraints = []
    constraints = [
        {
            "not_null": [
                {"value": "EMPLOYEES__ID"}
            ]
        }
    ]
    
    # Define two SQL queries to test
    sql1 = "SELECT * FROM EMPLOYEES"
    sql2 = "SELECT * FROM EMPLOYEES WHERE ID IS NOT NULL" # equivalent with not_null constraint, CEX found without not_null constraint
    
    # Configuration
    config = {
        'generate_code': True,
        'timer': True,
        'show_counterexample': True,
        'dialect': DIALECT.MYSQL,
        'all_null_is_deleted': False,
    }
    
    # Run verification
    try:
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
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    result = test_constraint()


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