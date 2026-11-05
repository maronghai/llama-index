# 07.01 父文档恢复与句子窗口

[返回全书目录 / Contents](../00-contents.md)

检索粒度与生成粒度不必相同。句子窗口检索用短句表示精确命中，再把周围句子作为生成上下文；父文档恢复先命中叶节点，再获取更完整的父段落。这样能保留条件和解释，避免把所有嵌入都扩大到整章。

句子窗口通常把窗口正文放在元数据中，后处理时替换节点内容；窗口字段应排除出嵌入，否则实际检索粒度又变大。层级方案需要持久化所有相关节点和父子关系。多个叶节点属于同一父块时应合并去重，再检查预算。

扩展得到的上下文仍必须满足授权与版本要求。不能因为某一句可见，就把包含受限内容的整个父文档一并送给模型。对混合权限文档，分块与访问边界要提前对齐。

## 重点与难点

重点：精确召回与完整生成分离。难点：扩展后的去重、权限和 token 预算。

## 面试考点与参考回答

问：为什么父块不直接做向量？答：父块可能过长并稀释语义；叶块负责定位，父块提供解释上下文，但需通过评测判断收益。

## 项目中的坑与处置

坑：只保存叶向量，没有父节点正文。处置：恢复测试覆盖父节点查找，构建时校验关系完整。

## 动手实验与验收

构造一条规则及后面的例外，比较仅句子、窗口和父块。验收：例外被保留，重复窗口不会重复消耗上下文。

## 代码实现补充：句子窗口恢复与父块授权

依赖：Python 3.10+；安装 `llama-index-core==0.14.25`。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

```python
from llama_index.core import Document
from llama_index.core.node_parser import SentenceWindowNodeParser
from llama_index.core.postprocessor import MetadataReplacementPostProcessor
from llama_index.core.schema import NodeWithScore

parser = SentenceWindowNodeParser.from_defaults(
    window_size=1, window_metadata_key="window", original_text_metadata_key="original",
    sentence_splitter=lambda text: [s.strip() + "." for s in text.split(".") if s.strip()])
doc = Document(text="Default limit is 500. Approved trips may use 800. Keep receipts.",
               metadata={"tenant": "a"})
nodes = parser.get_nodes_from_documents([doc])
hit = NodeWithScore(node=nodes[1], score=0.8)
assert hit.node.metadata["tenant"] == "a"
# Authorize every expanded source before applying this processor.
expanded = MetadataReplacementPostProcessor(target_metadata_key="window").postprocess_nodes([hit])
assert "500" in expanded[0].node.text and "800" in expanded[0].node.text
print(expanded[0].node.text)
```

### 实现说明、验收与项目边界

检索粒度是一句话，生成上下文扩展为相邻句。自定义切句函数使演示无需下载分句模型；生产需换成符合文档语言的句界识别。父块恢复同样必须验证扩展内容的租户与权限，不能只检查命中的子节点。

首次运行提示：核心包 tokenizer 可能下载编码缓存；离线环境请预置缓存并设置 `TIKTOKEN_CACHE_DIR`。无需模型密钥不代表首次运行不联网。
