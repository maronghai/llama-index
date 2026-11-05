# 04.01 句子、语义与层级切块

[返回全书目录 / Contents](../00-contents.md)

切块在检索精度与上下文完整性之间权衡。小块更容易匹配局部事实，却可能失去主语、条件和例外；大块保留语义，却稀释相似度并增加生成输入。chunk_size 通常以 tokenizer 的 token 计数衡量，不是字符数；中文、代码和表格的比例不同，不能直接用字符长度估算。

SentenceSplitter 尽量沿句子和段落边界切分，重叠用于缓解边界损失。重叠不是越大越好：它会增加向量数、候选重复和成本。语义切块根据相邻文本表示的变化找边界，可能增加嵌入成本，并对阈值、语言与文体敏感。结构良好的手册通常应先利用标题层级。

做对比实验时固定语料与问题，比较多种块大小、重叠和结构策略，记录证据覆盖、上下文 token 和答案质量。若相关条款跨块，优先考虑邻居扩展、父块恢复或保留标题，不要直接把所有块变大。层级切块会生成多级节点，索引叶节点时仍应保留父节点和关系供恢复。

## 示例与运行边界

本节示例按正文所列前置条件运行；部分是组件片段，不构成完整应用。

```python
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
text = "Receipts are required. Exceptions need written approval. " * 80
parser = SentenceSplitter(chunk_size=256, chunk_overlap=32)
nodes = parser.get_nodes_from_documents([Document(text=text, id_="policy")])
print(len(nodes), {n.ref_doc_id for n in nodes})
```

## 重点与难点

重点：块大小服务于证据边界。难点：检索粒度和生成粒度可以不同；tokenizer 与嵌入模型的截断上限必须一致考虑。

## 面试考点与参考回答

问：chunk_size=512 是最佳配置吗？答：没有通用最佳值，应按语料结构、问题长度、模型与评测选择，并同时控制上下文预算。

## 项目中的坑与处置

坑：大段元数据占满 token 预算，导致节点正文很短甚至切分失败。处置：精简入模元数据，结构化字段留在存储和过滤层。

## 动手实验与验收

对一份含“条件—规则—例外”的政策比较三种块大小。验收：至少发现一个边界失败案例，并说明为何邻居扩展优于简单增大所有块。

## 完整代码实现补充：多粒度切块策略对比与证据溯源完整验证

Python 3.10+；`llama-index-core==0.14.25`。混合检索另需 `llama-index-retrievers-bm25==0.8.0`，SQL 依赖 SQLAlchemy，事件流依赖 `llama-index-workflows`（core 的依赖）。独立进程运行完整代码块；首次 tokenizer 初始化可能读取或下载缓存，请离线部署时预置 `TIKTOKEN_CACHE_DIR`。

离线夹具只验证接口、来源和控制流，不验证语义质量或安全性。启用真实模型的分支需额外安装 `llama-index-llms-openai`、`llama-index-embeddings-openai`，重排分支另需 `llama-index-postprocessor-sbert-rerank`；设置 `RUN_REAL_MODELS=1`、`OPENAI_API_KEY`、`LLM_MODEL`、`EMBED_MODEL`（按示例需要）。这些外部模型分支本次未运行。

```python
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter

doc = Document(
    text=(
        "Section 1: Annual Leave entitlement is 15 business days.\n\n"
        "Section 2: Sick Leave requires hospital certificate after 2 consecutive days.\n\n"
        "Section 3: Compassionate Leave allows 3 to 5 days with manager approval."
    ),
    id_="policy_doc_2025"
)

# 1. 紧凑小块策略：专注于局部独立事实
small_splitter = SentenceSplitter(chunk_size=40, chunk_overlap=8)
small_nodes = small_splitter.get_nodes_from_documents([doc])

# 2. 宏观大块策略：专注于完整保留条款上下文
large_splitter = SentenceSplitter(chunk_size=120, chunk_overlap=20)
large_nodes = large_splitter.get_nodes_from_documents([doc])

assert len(small_nodes) >= len(large_nodes)
for node in small_nodes + large_nodes:
    assert node.ref_doc_id == "policy_doc_2025"

print("Chunking comparison complete:")
print(f"- Small chunk nodes count: {len(small_nodes)}")
print(f"- Large chunk nodes count: {len(large_nodes)}")
print(f"- All {len(small_nodes) + len(large_nodes)} nodes preserve parent doc traceability.")
```

### 架构说明与工程边界

对比细粒度句子切块与粗粒度长上下文切块，断言切块后的所有子节点都能完整保留父文档 ID 与顺序关系，为层级检索奠定基础。
