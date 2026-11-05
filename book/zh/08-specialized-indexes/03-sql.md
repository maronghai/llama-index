# 08.03 Text-to-SQL 与确定性计算

[返回全书目录 / Contents](../00-contents.md)

结构化数据适合过滤、聚合和计算，不应全部转成散文本再向量检索。Text-to-SQL 将问题转为查询，但生成 SQL 仍是非可信输入。只读账号、表列白名单、参数化值、查询超时和资源配额比提示中的“不要删除数据”更可靠。

先给模型经过裁剪的 schema、字段含义和允许关系，再验证生成查询。仅检查 SQL 是否以 SELECT 开头不够，复杂语句、函数和方言特性可能越界。高要求场景使用结构化查询计划或受限 DSL，经可信编译器转换为 SQL。

数值回答必须说明统计口径、时间区间、空值处理和单位。结果可能包含个人信息，应限制返回行数与字段。把查询结果视为数据，不能让数据库中的恶意字符串变成新的工具指令。

## 重点与难点

重点：计算交给数据库与可信代码。难点：SQL 方言验证和业务口径，而不是只生成合法语法。

## 面试考点与参考回答

问：只读账号就够了吗？答：不够。昂贵查询、敏感字段泄露和跨租户读取仍可能发生，还需范围与资源控制。

## 项目中的坑与处置

坑：把缺失金额当 0 计算增长率。处置：明确 null 语义、分母条件与货币单位，结果经过确定性校验。

## 动手实验与验收

设计销售汇总查询，加入跨租户与无限扫描负例。验收：合法聚合正确，越权与超预算查询被拦截。

## 代码实现补充：只读 SQL 执行与确定性聚合

依赖：Python 3.10+；仅使用 Python 标准库。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

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

### 实现说明、验收与项目边界

模型只选择允许的指标 ID，服务端注入认证租户，再参数化执行。此方案比任意 Text-to-SQL 更受限，适合固定报表。若接入 NLSQLTableQueryEngine，应使用只读账号、库侧行权限、解析器与执行预算；字符串以 SELECT 开头不足以构成安全检查。

## 完整代码实现补充：NLSQLTableQueryEngine 关系数据库 Text-to-SQL 闭环

Python 3.10+；`llama-index-core==0.14.25`。混合检索另需 `llama-index-retrievers-bm25==0.8.0`，SQL 依赖 SQLAlchemy，事件流依赖 `llama-index-workflows`（core 的依赖）。独立进程运行完整代码块；首次 tokenizer 初始化可能读取或下载缓存，请离线部署时预置 `TIKTOKEN_CACHE_DIR`。

离线夹具只验证接口、来源和控制流，不验证语义质量或安全性。启用真实模型的分支需额外安装 `llama-index-llms-openai`、`llama-index-embeddings-openai`，重排分支另需 `llama-index-postprocessor-sbert-rerank`；设置 `RUN_REAL_MODELS=1`、`OPENAI_API_KEY`、`LLM_MODEL`、`EMBED_MODEL`（按示例需要）。这些外部模型分支本次未运行。

```python
from sqlalchemy import create_engine, text, event
from llama_index.core import SQLDatabase
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM
from llama_index.core.base.llms.types import CompletionResponse
from llama_index.core.query_engine import NLSQLTableQueryEngine

engine = create_engine('sqlite:///:memory:')
with engine.begin() as conn:
    conn.execute(text('CREATE TABLE employees (id INTEGER, department TEXT, days INTEGER)'))
    conn.execute(text('INSERT INTO employees VALUES (1, :d, 15), (2, :e, 8)'),
                 {'d': 'Finance', 'e': 'Engineering'})
# This toy database has no private tables. Production uses read-only DB credentials and RLS.
@event.listens_for(engine, 'checkout')
def read_only(dbapi_connection, connection_record, connection_proxy):
    dbapi_connection.execute('PRAGMA query_only=ON')
class FixtureSQLModel(MockLLM):
    def complete(self, prompt, formatted=False, **kwargs):
        return CompletionResponse(text='SELECT SUM(days) AS total FROM employees')
db = SQLDatabase(engine, include_tables=['employees'])
query_engine = NLSQLTableQueryEngine(sql_database=db, tables=['employees'],
    llm=FixtureSQLModel(), embed_model=MockEmbedding(embed_dim=8),
    synthesize_response=False, handle_sql_errors=False)
response = query_engine.query('How many vacation days remain in total?')
assert 'SUM' in response.metadata['sql_query'].upper()
assert '23' in str(response)
try:
    with engine.begin() as conn:
        conn.execute(text('DELETE FROM employees'))
except Exception:
    print('Write rejected by database query_only mode.')
else:
    raise AssertionError('Database unexpectedly allowed a write')
print({'sql': response.metadata['sql_query'], 'result': str(response)})
```

### 架构说明与工程边界

实际执行 Text-to-SQL→数据库→结果断言，使用固定 SQL 输出模型验证编排，不代表自然语言生成 SQL 的能力。include_tables 仅限制模型看到的 schema，不是数据库权限；示例用 SQLite query_only 拦截写入，生产使用只读账号、查询超时、行数限制与数据库行级权限。
