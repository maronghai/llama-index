# 02.01 模块化安装与 Settings

[返回全书目录 / Contents](../00-contents.md)

LlamaIndex 的核心包与模型、读取器、向量库等集成包分别发布。安装 llama-index-core 不意味着已安装所有集成。示例应明确依赖分组，并记录实际验证过的 Python 与包版本；“最新”不是可复现的版本号。本书不宣称某个未测试的精确版本组合兼容。

Settings 为未显式传入组件的调用提供全局默认值，现代代码优先使用它替代旧 ServiceContext。构建索引前设置切块与嵌入配置；修改 Settings.chunk_size 不会重新切已有节点。嵌入模型变更也不会重建旧向量。不要依赖默认模型名来推断费用或维度。

多租户 Web 服务应在请求链路中显式传入模型、检索器和存储对象，避免按请求修改全局 Settings。全局变量在并发请求间共享，一个租户的配置可能污染另一个租户。配置应分为启动时只读默认值、索引构建清单和请求级授权参数。

## 示例与运行边界

以下为命令示例；请在独立实验环境执行并记录实际依赖版本。

```bash
# Illustrative installation commands; resolve and pin a tested set in your environment.
python -m pip install llama-index-core
python -m pip freeze
# Later examples name their additional integration packages where needed.
```

## 重点与难点

重点：核心与集成分开安装，配置显式化。难点：配置变化与已生成数据之间没有自动的双向同步。

## 面试考点与参考回答

问：为什么同一段代码换机器就失败？答：可能是集成包缺失、版本漂移、模型服务差异或隐式默认值；先记录依赖和配置，再定位导入、构建或请求阶段。

## 项目中的坑与处置

坑：Notebook 一直运行正常，重启后报缺少模型凭据。处置：把启动配置写成显式步骤，使用环境变量读取凭据，禁止把密钥写入书稿或日志。

## 动手实验与验收

在独立虚拟环境安装核心与需要的集成，记录 pip freeze 和 Python 版本。验收：全新进程能完成导入，且运行说明区分离线与外部服务依赖。

## 代码实现补充：显式配置与运行环境指纹

依赖：Python 3.10+；安装 `llama-index-core==0.14.25`。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

```python
import sys
from importlib.metadata import version
from llama_index.core import Settings, Document, VectorStoreIndex
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM

Settings.llm = MockLLM(max_tokens=16)
Settings.embed_model = MockEmbedding(embed_dim=8)
Settings.chunk_size = 128
Settings.chunk_overlap = 16
index = VectorStoreIndex.from_documents([Document(text="A reproducible offline baseline.")])
assert index.as_retriever(similarity_top_k=1).retrieve("baseline")
print({"python": sys.version.split()[0], "core": version("llama-index-core"),
       "embedding_dim": 8, "chunk_size": Settings.chunk_size})
```

### 实现说明、验收与项目边界

在独立进程运行，避免全局 Settings 影响其他实验。生产多租户服务应把不同模型作为构造参数注入。保存输出指纹，但还要额外记录语料哈希、模型版本及 tokenizer；一个核心包版本不足以复现实验。

首次运行提示：核心包 tokenizer 可能下载编码缓存；离线环境请预置缓存并设置 `TIKTOKEN_CACHE_DIR`。无需模型密钥不代表首次运行不联网。
