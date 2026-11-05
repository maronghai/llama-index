# 06.03 重排、阈值与流式响应

[返回全书目录 / Contents](../00-contents.md)

Cross-encoder 对查询与候选文本联合编码，通常比单独向量相似度更能识别细粒度相关性，但增加候选逐对计算成本。先粗召回，再对有限候选重排，最后按上下文预算选证据。重排不能恢复从未召回的节点，也不自动验证来源权威或时间适用性。

阈值要按业务与分数语义标定。过高会漏答，过低会给无答案问题硬找材料。记录拒答率、误拒率和错误回答率的权衡，必要时用额外的证据充分性分类，而不是单个相似度值。对长块检查重排器输入截断，否则例外可能在不可见的尾部。

流式输出降低首 token 等待感，但不减少全部计算，也不保证总延迟更低。部分合成模式可能先完成多次非流式调用再输出最终流。流式接口还要处理断连、取消、背压和错误事件。高风险答案在校验前就展示不可撤回的片段，可能形成错误承诺，应选择先校验再输出关键结论。

## 重点与难点

重点：候选召回、重排、预算选择各自优化。难点：首 token 延迟与总延迟不同，流式内容的校验时机影响产品行为。

## 面试考点与参考回答

问：重排后质量下降为什么？答：可能候选已错、重排模型不懂领域、截断丢失条件，或 top-n 太小；检查成对样例而非盲目换模型。

## 项目中的坑与处置

坑：客户端断连后服务器继续完整生成。处置：传播取消信号，清理资源，并把被取消请求和正常完成分开统计。

## 动手实验与验收

测量无重排与重排的候选命中、首 token 和总延迟，再模拟断连。验收：能证明质量收益是否值得新增延迟，取消确实终止工作。

## 代码实现补充：候选重排、空分数与流式边界

依赖：Python 3.10+；安装 `llama-index-core==0.14.25`。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

```python
from llama_index.core.schema import TextNode, NodeWithScore

def lexical_rerank(question, candidates):
    terms = set(question.lower().split())
    def score(hit):
        return len(terms & set(hit.node.text.lower().split())) / max(1, len(terms))
    return sorted([(score(h), h) for h in candidates], key=lambda x: x[0], reverse=True)

def stream_selected(question, candidates, threshold=0.5):
    ranked = lexical_rerank(question, candidates)
    if not ranked or ranked[0][0] < threshold:
        yield "Insufficient evidence"
        return
    # Evidence is selected before the first visible token.
    for word in ranked[0][1].node.text.split():
        yield word + " "

candidates = [NodeWithScore(node=TextNode(text="office lunch noon"), score=None),
              NodeWithScore(node=TextNode(text="hotel allowance 500"), score=0.6)]
result = "".join(stream_selected("hotel allowance", candidates))
assert result.strip() == "hotel allowance 500"
assert "Insufficient" in "".join(stream_selected("payroll", candidates))
print(result)
```

### 实现说明、验收与项目边界

词重合只是可解释的重排替身，不是 Cross-Encoder，也不适合直接处理未分词中文。真实项目可替换为 SentenceTransformerRerank，安装相应 postprocessor 集成并预置模型。阈值针对此重排器标定，不能混用向量距离；此处展示的是分块输出边界，并未调用模型流式接口。

首次运行提示：核心包 tokenizer 可能下载编码缓存；离线环境请预置缓存并设置 `TIKTOKEN_CACHE_DIR`。无需模型密钥不代表首次运行不联网。

## 完整代码实现补充：基于 SimilarityPostprocessor 的置信度截断后处理流水线

Python 3.10+；`llama-index-core==0.14.25`。混合检索另需 `llama-index-retrievers-bm25==0.8.0`，SQL 依赖 SQLAlchemy，事件流依赖 `llama-index-workflows`（core 的依赖）。独立进程运行完整代码块；首次 tokenizer 初始化可能读取或下载缓存，请离线部署时预置 `TIKTOKEN_CACHE_DIR`。

离线夹具只验证接口、来源和控制流，不验证语义质量或安全性。启用真实模型的分支需额外安装 `llama-index-llms-openai`、`llama-index-embeddings-openai`，重排分支另需 `llama-index-postprocessor-sbert-rerank`；设置 `RUN_REAL_MODELS=1`、`OPENAI_API_KEY`、`LLM_MODEL`、`EMBED_MODEL`（按示例需要）。这些外部模型分支本次未运行。

```python
import os
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.schema import NodeWithScore, TextNode

# Controlled scores verify the threshold contract, independent of model calibration.
candidates = [NodeWithScore(node=TextNode(text='Restart the server.'), score=0.9),
              NodeWithScore(node=TextNode(text='Cafeteria menu.'), score=0.2)]
filtered = SimilarityPostprocessor(similarity_cutoff=0.7).postprocess_nodes(candidates)
assert len(filtered) == 1 and filtered[0].node.text == 'Restart the server.'

real = os.getenv('RUN_REAL_MODELS') == '1'
if real:
    from llama_index.embeddings.openai import OpenAIEmbedding
    from llama_index.llms.openai import OpenAI
    from llama_index.core.postprocessor import SentenceTransformerRerank
    embed = OpenAIEmbedding(model=os.environ['EMBED_MODEL'])
    llm = OpenAI(model=os.environ['LLM_MODEL'], timeout=30, max_retries=1)
    # Set RERANK_MODEL to a previously provisioned local model directory.
    reranker = SentenceTransformerRerank(model=os.environ['RERANK_MODEL'], top_n=1)
    processors = [reranker]
else:
    embed, llm = MockEmbedding(embed_dim=8), MockLLM(max_tokens=16)
    processors = []
index = VectorStoreIndex.from_documents([
    Document(text='Restart: drain requests, restart one replica, check health.'),
    Document(text='Cafeteria serves lunch at noon.')], embed_model=embed)
engine = index.as_query_engine(llm=llm, similarity_top_k=2,
                              node_postprocessors=processors, streaming=True)
response = engine.query('How should I restart a server?')
parts = []
for delta in response.response_gen:
    print(delta, end='', flush=True)
    parts.append(delta)
assert parts and response.source_nodes
print(chr(10), {'sources': len(response.source_nodes), 'real_reranker': real})
```

### 架构说明与工程边界

阈值过滤、Cross-Encoder 重排与真正的生成器流式输出均有入口。默认只测试阈值和流式接口，不测试重排质量；RUN_REAL_MODELS=1 时启用真实嵌入、模型及本地 Cross-Encoder。RRF 分数不能直接套用向量阈值。
