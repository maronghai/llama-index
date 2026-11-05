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
