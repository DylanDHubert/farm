import sys
sys.path.insert(0, 'src')

from farmer import Farmer

# Load data
f = Farmer()
f.load_document('test', 'data/pb&j_20250626_173624/final_output.json')

# Get table
table = f.get_table_by_id('table_1')
print(f'Table found: {table is not None}')
print(f'Table ID: {table["table_id"]}')
print(f'Rows: {len(table["rows"])}')

# Debug search
print('\nDebug search:')
for i, row in enumerate(table['rows']):
    print(f'Row {i}:')
    for key, value in row.items():
        print(f'  {key}: {value} (type: {type(value)})')
    print('---')

# Test search
print('\nTesting search:')
results = f.search_table_values('table_1', 'Mayonnaise')
print(f'Found {len(results)} results for "Mayonnaise"')

# Test with different terms
for term in ['Mayonnaise', 'mayo', 'TRUE', 'FALSE']:
    results = f.search_table_values('table_1', term)
    print(f'"{term}": {len(results)} results') 