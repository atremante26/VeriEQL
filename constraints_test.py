import sys
import os

# Setup paths
base_dir = "/home/hwu/txt2sql-verieql/VeriEQL"
sys.path.insert(0, base_dir)

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
    constraints = [
        # Existing constraint types for reference:
        {'primary': ['EMPLOYEES__ID']},
        {'between': [['EMPLOYEES__AGE'], 18, 65]},
        
        # Add your new constraint here:
    ]
    
    # Define two SQL queries to test
    sql1 = "SELECT * FROM EMPLOYEES WHERE SALARY > 50000"
    sql2 = "SELECT * FROM EMPLOYEES WHERE SALARY > 50000"  # Should be equivalent
    
    # Configuration
    config = {
        'generate_code': False,
        'timer': True,
        'show_counterexample': True,
        'dialect': DIALECT.MYSQL,
        'all_null_is_deleted': True,
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
    print(result)