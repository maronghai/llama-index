# 08.03 Text-to-SQL and deterministic computation

[返回全书目录 / Contents](../00-contents.md)

Structured data is suited to filtering and aggregation rather than being flattened entirely into vector chunks. Text-to-SQL generates untrusted SQL. Read-only accounts, schema allowlists, parameterized values, timeouts, and resource limits provide stronger controls than a prompt requesting safe behavior.

Provide a scoped schema with field meanings and allowed joins, then validate queries. Checking only for a SELECT prefix is insufficient because dialect features and functions can exceed intended scope. Stronger designs generate a restricted plan or DSL compiled by trusted code.

Numeric answers need aggregation definitions, time windows, null handling, and units. Restrict rows and columns to limit sensitive output. Treat database strings as data, never as new tool instructions.

## Key points and difficulties

Key: delegate computation to databases and trusted code. Difficulty: dialect-aware validation and business semantics, not mere syntax.

## Interview question and answer

Q: Is a read-only account sufficient? A: no. Expensive queries, sensitive fields, and cross-tenant reads still need scope and resource controls.

## Production pitfalls and mitigation

Pitfall: converting missing amounts to zero in growth calculations. Define nulls, denominator rules, and currency, then validate deterministically.

## Exercise and acceptance criteria

Design a sales aggregation with cross-tenant and full-scan negative cases. Acceptance: correct allowed results and blocked unauthorized or over-budget queries.

## Implementation supplement: Read-only SQL execution and deterministic aggregation

Dependencies: Python 3.10+; Python standard library only.

Save the complete block as a standalone `.py` file and execute it in a separate process with `python filename.py`. No API key or paid model call is required. Assertions must pass and results are printed.

```python
import sqlite3

con = sqlite3.connect(":memory:")
con.execute("CREATE TABLE expenses (tenant TEXT, amount INTEGER)")
con.executemany("INSERT INTO expenses VALUES (?, ?)", [("a", 120), ("a", 80), ("b", 999)])
con.commit()
con.execute("PRAGMA query_only=ON")
# The model selects a metric ID, never arbitrary executable SQL.
queries = {"expense_total": "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE tenant = ?"}

def compute(metric, tenant):
    if metric not in queries:
        raise ValueError("unknown metric")
    return con.execute(queries[metric], (tenant,)).fetchone()[0]

assert compute("expense_total", "a") == 200
assert compute("expense_total", "a' OR 1=1 --") == 0
try:
    con.execute("DELETE FROM expenses")
except sqlite3.OperationalError:
    print("write denied")
else:
    raise AssertionError("write protection failed")
print(compute("expense_total", "a"))
con.close()
```

### Implementation, acceptance and production boundaries

The model selects an allowlisted metric ID; the server supplies the authenticated tenant and parameterized execution. This suits fixed reports. NLSQLTableQueryEngine requires read-only credentials, database row policies, SQL parsing and execution budgets. A SELECT prefix is not a security check.
