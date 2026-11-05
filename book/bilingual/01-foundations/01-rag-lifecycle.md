# 01.01 RAG 的生命周期与系统边界 / The RAG lifecycle and system boundaries

[返回全书目录 / Contents](../00-contents.md)

RAG 把回答依据从模型参数扩展到外部证据。离线链路负责加载、解析、切块、向量化和发布索引；在线链路负责身份校验、检索、重排、上下文组装和生成。评估贯穿两条链路，而不是上线前才运行一次。LlamaIndex 组织这些组件，但不会自动保证文档正确、权限安全或答案可信。

RAG extends the evidence available to a model beyond its parameters. The offline path loads, parses, chunks, embeds, and publishes data. The online path authenticates callers, retrieves and reranks evidence, assembles context, and generates answers. Evaluation spans both paths. LlamaIndex organizes these components; correctness, authorization, and answer quality remain application responsibilities.

例如员工询问“出差住宿上限是多少”，系统必须先确定地区、员工适用范围和制度生效日期，再检索对应条款。只找语义最相似的文本，可能返回去年制度或其他地区的规定。把“找得像”和“适用于这个问题”分开，是理解生产 RAG 的第一步。

For a travel-policy question, the system must establish the applicable region, employee group, and effective date before selecting evidence. Semantic similarity alone may return last year’s rules or another region’s policy. Separating similarity from applicability is the first production design decision.

把系统拆成可观测的边界：原始文件快照、标准化文档、节点集合、索引版本、检索结果和最终回答。每个边界记录输入版本与耗时。回答失败时先检查证据链：源数据是否有答案、解析是否保留答案、检索是否找到答案、生成是否忠实使用答案。

Expose observable boundaries: source snapshots, normalized documents, nodes, index releases, retrieval results, and final answers. Record input versions and latency at each boundary. Diagnose failures by asking whether the source contained the answer, parsing preserved it, retrieval found it, and generation used it faithfully.

## 重点与难点 / Key points and difficulties

重点：离线构建与在线查询分离。难点：把答案质量拆成数据覆盖、检索质量和生成忠实性，避免用单一“准确率”遮住问题。

Key: separate offline construction from online queries. Difficulty: distinguish source coverage, retrieval quality, and generation faithfulness instead of hiding all failures behind one accuracy number.

## 面试考点与参考回答 / Interview question and answer

问：RAG 与微调怎么选？答：频繁更新、需要出处的知识优先外部检索；稳定的输出格式或行为可考虑微调。两者可以组合，微调不能替代实时权限与知识更新。

Q: RAG or fine-tuning? A: retrieval suits changing knowledge and cited answers; fine-tuning may improve stable behavior or output style. They can be combined. Fine-tuning does not replace live authorization or knowledge updates.

## 项目中的坑与处置 / Production pitfalls and mitigation

坑：先上线聊天页面，再补数据治理，导致每次修复都要返工。处置：从一开始给文档稳定 ID、版本、来源和访问范围，并保留无答案样例。

Pitfall: shipping chat before governing data makes every correction expensive. Assign stable IDs, versions, provenance, and access scopes from the beginning, and include unanswerable questions in the dataset.

## 动手实验与验收 / Exercise and acceptance criteria

画出一个制度问答系统的离线与在线数据流；在六个边界标出输入、输出和失败处理。验收：能分别解释“没读到”“没检到”和“编造了”。

Draw both paths of a policy assistant and specify inputs, outputs, and failures at six boundaries. Acceptance: clearly distinguish ingestion loss, retrieval misses, and unsupported generation.

## 代码实现补充 / Implementation supplement: 从文档到证据的离线闭环 / An offline document-to-evidence lifecycle

依赖 / Dependencies: Python 3.10+; `llama-index-core==0.14.25`。

将完整代码保存为独立 `.py` 文件，在独立进程执行 `python filename.py`。无需密钥，无付费调用；验收为断言通过并输出结果。

Save the full block as a standalone `.py` file and run it in a separate process. No API key or paid call is needed; assertions must pass and results are printed.

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

### 实现说明、验收与项目边界 / Implementation, acceptance and production boundaries

文档 ID → 节点来源 → 检索证据 → 响应来源构成可检查链路。断言只证明对象连接正确；MockEmbedding 的排名和 MockLLM 的回答均不能证明语义质量。下一步替换真实嵌入，并用带标准证据的查询集评估。

Document IDs, node source references, retrieved evidence and response sources form an auditable chain. Assertions check connectivity only. Neither mock rankings nor mock answers establish quality; replace embeddings and evaluate against labeled evidence.

首次运行 / First run：tokenizer 可能下载编码缓存。离线运行需预置缓存并设置 `TIKTOKEN_CACHE_DIR`。Tokenization may download an encoding cache; provision it before offline use.
