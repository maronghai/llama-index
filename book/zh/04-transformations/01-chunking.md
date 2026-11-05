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
