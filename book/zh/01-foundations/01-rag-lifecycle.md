# 01.01 RAG 的生命周期与系统边界

[返回全书目录 / Contents](../00-contents.md)

RAG 把回答依据从模型参数扩展到外部证据。离线链路负责加载、解析、切块、向量化和发布索引；在线链路负责身份校验、检索、重排、上下文组装和生成。评估贯穿两条链路，而不是上线前才运行一次。LlamaIndex 组织这些组件，但不会自动保证文档正确、权限安全或答案可信。

例如员工询问“出差住宿上限是多少”，系统必须先确定地区、员工适用范围和制度生效日期，再检索对应条款。只找语义最相似的文本，可能返回去年制度或其他地区的规定。把“找得像”和“适用于这个问题”分开，是理解生产 RAG 的第一步。

把系统拆成可观测的边界：原始文件快照、标准化文档、节点集合、索引版本、检索结果和最终回答。每个边界记录输入版本与耗时。回答失败时先检查证据链：源数据是否有答案、解析是否保留答案、检索是否找到答案、生成是否忠实使用答案。

## 重点与难点

重点：离线构建与在线查询分离。难点：把答案质量拆成数据覆盖、检索质量和生成忠实性，避免用单一“准确率”遮住问题。

## 面试考点与参考回答

问：RAG 与微调怎么选？答：频繁更新、需要出处的知识优先外部检索；稳定的输出格式或行为可考虑微调。两者可以组合，微调不能替代实时权限与知识更新。

## 项目中的坑与处置

坑：先上线聊天页面，再补数据治理，导致每次修复都要返工。处置：从一开始给文档稳定 ID、版本、来源和访问范围，并保留无答案样例。

## 动手实验与验收

画出一个制度问答系统的离线与在线数据流；在六个边界标出输入、输出和失败处理。验收：能分别解释“没读到”“没检到”和“编造了”。

## 代码实现补充：从文档到证据的离线闭环

依赖：Python 3.10+；安装 `llama-index-core==0.14.25`。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

```python
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM
from llama_index.core.node_parser import SentenceSplitter

docs = [Document(text="Travel lodging limit is 500 CNY per night.",
                 id_="travel-v2", metadata={"revision": "2"})]
nodes = SentenceSplitter(chunk_size=64, chunk_overlap=8).get_nodes_from_documents(docs)
index = VectorStoreIndex(nodes, embed_model=MockEmbedding(embed_dim=8))
hits = index.as_retriever(similarity_top_k=1).retrieve("What is the lodging limit?")
assert hits and hits[0].node.ref_doc_id == "travel-v2"
response = index.as_query_engine(llm=MockLLM(max_tokens=32)).query("Lodging limit?")
assert response.source_nodes
print({"documents": len(docs), "nodes": len(nodes), "sources": len(response.source_nodes)})
```

### 实现说明、验收与项目边界

文档 ID → 节点来源 → 检索证据 → 响应来源构成可检查链路。断言只证明对象连接正确；MockEmbedding 的排名和 MockLLM 的回答均不能证明语义质量。下一步替换真实嵌入，并用带标准证据的查询集评估。

首次运行提示：核心包 tokenizer 可能下载编码缓存；离线环境请预置缓存并设置 `TIKTOKEN_CACHE_DIR`。无需模型密钥不代表首次运行不联网。
