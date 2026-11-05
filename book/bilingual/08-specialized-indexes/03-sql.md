# 08.03 Text-to-SQL 与确定性计算 / Text-to-SQL and deterministic computation

[返回全书目录 / Contents](../00-contents.md)

结构化数据适合过滤、聚合和计算，不应全部转成散文本再向量检索。Text-to-SQL 将问题转为查询，但生成 SQL 仍是非可信输入。只读账号、表列白名单、参数化值、查询超时和资源配额比提示中的“不要删除数据”更可靠。

Structured data is suited to filtering and aggregation rather than being flattened entirely into vector chunks. Text-to-SQL generates untrusted SQL. Read-only accounts, schema allowlists, parameterized values, timeouts, and resource limits provide stronger controls than a prompt requesting safe behavior.

先给模型经过裁剪的 schema、字段含义和允许关系，再验证生成查询。仅检查 SQL 是否以 SELECT 开头不够，复杂语句、函数和方言特性可能越界。高要求场景使用结构化查询计划或受限 DSL，经可信编译器转换为 SQL。

Provide a scoped schema with field meanings and allowed joins, then validate queries. Checking only for a SELECT prefix is insufficient because dialect features and functions can exceed intended scope. Stronger designs generate a restricted plan or DSL compiled by trusted code.

数值回答必须说明统计口径、时间区间、空值处理和单位。结果可能包含个人信息，应限制返回行数与字段。把查询结果视为数据，不能让数据库中的恶意字符串变成新的工具指令。

Numeric answers need aggregation definitions, time windows, null handling, and units. Restrict rows and columns to limit sensitive output. Treat database strings as data, never as new tool instructions.

## 重点与难点 / Key points and difficulties

重点：计算交给数据库与可信代码。难点：SQL 方言验证和业务口径，而不是只生成合法语法。

Key: delegate computation to databases and trusted code. Difficulty: dialect-aware validation and business semantics, not mere syntax.

## 面试考点与参考回答 / Interview question and answer

问：只读账号就够了吗？答：不够。昂贵查询、敏感字段泄露和跨租户读取仍可能发生，还需范围与资源控制。

Q: Is a read-only account sufficient? A: no. Expensive queries, sensitive fields, and cross-tenant reads still need scope and resource controls.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：把缺失金额当 0 计算增长率。处置：明确 null 语义、分母条件与货币单位，结果经过确定性校验。

Pitfall: converting missing amounts to zero in growth calculations. Define nulls, denominator rules, and currency, then validate deterministically.

## 动手实验与验收 / Exercise and acceptance criteria

设计销售汇总查询，加入跨租户与无限扫描负例。验收：合法聚合正确，越权与超预算查询被拦截。

Design a sales aggregation with cross-tenant and full-scan negative cases. Acceptance: correct allowed results and blocked unauthorized or over-budget queries.

## 代码实现补充 / Implementation supplement: 只读 SQL 执行与确定性聚合 / Read-only SQL execution and deterministic aggregation

依赖 / Dependencies: Python 3.10+; 仅标准库 / standard library only.

将完整代码保存为独立 `.py` 文件，在独立进程执行 `python filename.py`。无需密钥，无付费调用；验收为断言通过并输出结果。

Save the full block as a standalone `.py` file and run it in a separate process. No API key or paid call is needed; assertions must pass and results are printed.

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

### 实现说明、验收与项目边界 / Implementation, acceptance and production boundaries

模型只选择允许的指标 ID，服务端注入认证租户，再参数化执行。此方案比任意 Text-to-SQL 更受限，适合固定报表。若接入 NLSQLTableQueryEngine，应使用只读账号、库侧行权限、解析器与执行预算；字符串以 SELECT 开头不足以构成安全检查。

The model selects an allowlisted metric ID; the server supplies the authenticated tenant and parameterized execution. This suits fixed reports. NLSQLTableQueryEngine requires read-only credentials, database row policies, SQL parsing and execution budgets. A SELECT prefix is not a security check.
