# 企业知识库：部署、接口与运维

这是与本书配套的完整单节点 RAG 项目。它使用真实 LlamaIndex 检索组件，包含可运行 API、持久化、权限、版本控制、测试与容器入口。支持中英文文本输入。当前面向受控规模的内部知识库，不代表已完成企业现场的安全审计、压测或高可用验收。

## 1. 五分钟运行（Windows PowerShell）

在本项目目录运行。建议使用独立 Python 3.12 环境。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe install.py
.\.venv\Scripts\python.exe run.py demo
.\.venv\Scripts\python.exe run.py evaluate
.\.venv\Scripts\python.exe -m pytest tests -v
```

演示和评估会自动生成随机身份凭证、创建临时数据库、执行两个租户的摄取和查询、验证未知问题拒答，然后清理演示数据。离线模式使用确定性哈希向量和证据摘录，不依赖模型账号，不下载词典或模型。它用于验证链路和隔离，不能作为语义召回或答案质量的正式基线。

启动长期运行的服务前，在当前终端生成随机密钥并设置身份映射：

```powershell
$key = .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
$env:KB_KEYS_JSON = @{ $key = @{ tenant = 'alpha'; role = 'admin' } } | ConvertTo-Json -Compress
$env:KB_DB = 'data/knowledge.db'
.\.venv\Scripts\python.exe run.py serve
```

不要把密钥提交到代码库或作为命令行参数传递。真实部署由密钥管理系统注入 `KB_KEYS_JSON`。配置文件中没有内置演示密钥；不配置身份映射，服务拒绝启动。

## 2. 目录与关键实现

| 文件 | 作用 |
|---|---|
| `kb/config.py` | 环境变量、角色、向量和切块契约 |
| `kb/models.py` | LlamaIndex BaseEmbedding 适配器、中文词元、远程模型超时和引用校验 |
| `kb/store.py` | SQLite WAL、原子摄取、版本乐观锁、审计、限流、证据版本复查 |
| `kb/retrieval.py` | TextNode、VectorStoreIndex、BM25、RRF、带引用回答 |
| `kb/api.py` | FastAPI、鉴权、角色边界、输入限制、请求追踪与错误映射 |
| `demo.py` | 无外部依赖服务的端到端验收场景 |
| `run.py` | demo / evaluate / serve / backup / worker 命令 |
| `kb/worker.py` | 持久化摄取任务、租约续期、重试和退出信号 |
| `tests/test_jobs.py` | 幂等、恢复、取消、并发认领、配额、版本和分页测试 |
| `tests/test_service.py` | 权限、隔离、并发、删除、故障、重启与恢复测试 |
| `Dockerfile` | 非 root 容器入口、健康探针 |
| `install.py` | 固定已验证的直接依赖版本 |

请求处理链：认证 → 服务端租户绑定 → 数据库限流 → 读取授权快照 → LlamaIndex 向量检索与 BM25 → RRF → 回答与引用 → 证据版本复查 → 返回。

写入链：校验文本 → 切块与计算向量 → 事务中检查 expected_version → 文档、向量和审计一起提交。模型故障发生在事务前，旧版本保持可用。相同内容在正确版本下写入不会增加版本号，但仍会记录幂等审计；当前实现仍会先计算向量，不应把它称为免模型调用缓存。

## 3. API 契约与调用

所有业务接口要求 `Authorization: Bearer <随机密钥>`。身份映射取自服务器配置，不接受客户端 tenant 字段。`reader` 只读，`writer` 可写，`admin` 在同一租户内增加审计读取权限，admin 不能跨租户查询。

| 方法 | 路由 | 输入与行为 |
|---|---|---|
| GET | `/health/live` | 存活探针，不鉴权 |
| GET | `/health/ready` | SQLite 连通性，不鉴权；不探测外部模型 |
| GET | `/v1/documents` | 当前租户文档元信息，limit/after 游标分页，不返回全文 |
| PUT | `/v1/documents/{id}` | title、text、expected_version；新建版本为0，更新必须传现有版本 |
| DELETE | `/v1/documents/{id}` | JSON expected_version；提交后新查询不再命中文档 |
| POST | `/v1/query` | question、top_k（1至10）；返回 answer、refused、citations、request_id |
| GET | `/v1/audit` | 当前租户审计，limit/before 游标分页，仅admin |

服务默认关闭交互式接口文档，接口以此表与源码输入模型为准。所有 SQL 参数绑定；id 是数据库键，不作为文件路径。正文大小上限900000字节，文档最多200000字符，问题最多2000字符，租户默认最多5000个切块。

在另外的 PowerShell 终端，通过安全方式注入同一密钥后调用：

```powershell
$headers = @{ Authorization = "Bearer $env:KB_CLIENT_KEY" }
$base = $env:KB_SERVICE_URL
$doc = @{ title='差旅制度'; text='差旅酒店报销上限为每晚600元。'; expected_version=0 } | ConvertTo-Json
Invoke-RestMethod "$base/v1/documents/travel" -Method Put -Headers $headers -Body ([Text.Encoding]::UTF8.GetBytes($doc)) -ContentType 'application/json'
$q = @{ question='差旅酒店报销上限是多少？'; top_k=4 } | ConvertTo-Json
Invoke-RestMethod "$base/v1/query" -Method Post -Headers $headers -Body ([Text.Encoding]::UTF8.GetBytes($q)) -ContentType 'application/json'
```

版本号从写入响应和文档列表中获取。更新传1得到2；过期写入或删除返回409。相同内容重试应带当前版本；同步接口没有独立 Idempotency-Key，不保证客户端超时后盲目重放得到相同响应。需要可靠重试时使用异步摄取接口的 idempotency_key；同步接口使用固定文档id并查询版本进行对账。删除后重建仍传 expected_version=0，但返回版本从历史最大值继续递增。

错误约定：401无凭证、403权限不足、404文档不存在、409版本或证据变化、413正文或租户容量超限、422输入不合约、429频次限制、503模型不可用、500其他故障。错误响应不返回密钥、文档或模型服务内部错误。

## 4. 接入真实模型

支持提供 `/embeddings` 与 `/chat/completions` 的 HTTPS 模型网关。使用你自己的合法服务账号；示例不预设服务商或模型名称。

```powershell
$env:KB_MODE = 'remote'
# 从密钥管理系统注入 KB_MODEL_BASE 和 KB_MODEL_KEY
# KB_MODEL_BASE 应包含网关 API 前缀，例如网关文档规定的 v1 前缀
$env:KB_EMBEDDING_MODEL = '<实际嵌入模型名>'
$env:KB_CHAT_MODEL = '<实际聊天模型名>'
$env:KB_EMBEDDING_DIM = '<嵌入模型实际维度>'
$env:KB_DB = 'data/remote-knowledge.db'
.\.venv\Scripts\python.exe run.py serve
```

每次模型请求明确设置超时25秒，禁用重定向。外部模型故障返回503，不伪造成功、不静默降级到离线模型。为避免超时重试放大成本，当前只进行一次模型调用；客户端可对503做带抖动、有预算的重试。除同步接口外，现已提供持久化异步摄取队列；不提供大文件分片上传或断点续传。远程 HTTP 合约在自动化测试中使用模拟响应验证，没有使用真实模型账号做实测。

更换嵌入模型、维度、网关、模式或切块契约必须重建数据库并重新摄取。启动时契约不一致会直接拒绝，避免新旧向量混用。保留旧数据库，验收新库后切换配置，回滚时切回原库。固定维度、模型名称并不能阻止供应商暗中更新模型，生产应使用供应商的不可变模型版本。

## 5. 部署和容量边界

容器按非root运行，数据挂载目录需允许UID 10001读写。启动环境变量使用受控环境文件或编排平台密钥注入，不复制到镜像。

```bash
docker build -t book-kb:1 .
docker run --rm --name book-kb --env-file /secure/kb.env --mount type=volume,source=kb-data,target=/data -p 8000:8000 book-kb:1
```

当前交付的持久向量库是SQLite，并在每次查询时只对当前租户的切块构建内存VectorStoreIndex。文本和向量同事务，删除传播简单；代价是查询复杂度随租户切块量增加。不要将其宣称为百万级向量服务。5000切块是保护性上限，实际QPS、延迟和内存容量必须用自己的文档及模型压测。

API默认单进程、单副本，另起本机worker进程；任务允许多个本机worker互斥认领。SQLite数据必须在本机可靠磁盘，不放网络共享盘。数据库限流按密钥和固定分钟窗口计数，多个密钥可叠加额度，不等于计费配额或全局租户限流。服务入口前放TLS终止、连接数限制、超时、访问控制和请求体限制；运行进程使用专用系统账号和最小文件权限。当前未实现SSO、文档级ACL、共享知识库、会话记忆、Agent工具执行、图检索或SQL生成，这些属于后续独立功能，不冒充已实现。

生产迁移到外部向量数据库时，必须保留租户过滤下推、证据二次授权、更新/删除对账；SQLite与外部向量存储不再能用同一事务，应增加outbox事件与幂等工作者。

`install.py` 固定直接依赖，传递依赖未锁定。容器基础镜像也未固定摘要。正式供应链发布应在自己的受控环境生成完整依赖锁、镜像摘要与软件物料清单；本次没有擅自添加这些配置。

## 6. 观测、告警与数据安全

HTTP日志只写请求id、方法、状态和耗时，不记录Authorization、问题正文、证据或模型文本。审计表只保存租户、密钥摘要标识、动作、文档id和请求id，不保存原始密钥。通过标准输出收集日志，按请求id追踪，监测5xx/409/429比例及耗时分位数。探针只确认应用与数据库，外部模型可用性需单独受控探测。

SQLite没有内置加密，需依赖磁盘与备份加密、目录权限及主机安全；审计与备份的保留期限由企业策略规定。DELETE移除主表和切块，但SQLite空闲页、WAL及历史备份可能仍残留旧内容，不能声称是合规物理擦除；按法规要求制定加密密钥销毁、备份过期和离线压缩策略。

模型提示词要求把检索内容作为数据，并检查返回引用编号是否存在。该校验只保证引用结构合法，不能证明每句话受证据支持，也无法彻底阻止提示注入。项目没有任意工具执行路径；对真实生成内容仍需红队样本和人工抽检。

## 7. 备份、恢复与故障处理

使用SQLite在线backup API，不直接复制正在运行的db/WAL文件。

```powershell
.\.venv\Scripts\python.exe run.py backup --output 'backups/knowledge-20261105.db'
```

备份目标必须不存在。恢复时停止服务，把KB_DB指向备份副本，使用同样的索引契约启动；验证授权隔离、文档版本和抽样引用后恢复入口。本次启动会以幂等建表方式新增任务表、版本墓碑表和索引，回填当前文档版本并记录 user_version=2；旧文档和索引契约保留。历史已删除文档无法回溯墓碑。发布前停止旧worker并备份，在数据库副本验证后切换；这不是通用迁移/降级框架。

| 现象 | 优先检查与处置 |
|---|---|
| 启动契约不一致 | 不覆盖旧库；检查模式、模型、维度和切块版本，重新摄取到新库 |
| 409写入冲突 | 读当前版本，对比业务内容后重新提交，不强行覆盖 |
| 409查询证据变化 | 摄取或删除与生成并发，重新检索后重试 |
| 503模型失败 | 排查网关状态、凭证、维度和超时；旧库保持不变 |
| 429 | 按Retry-After退避；不要循环创建新密钥绕过限流 |
| 查询变慢 | 检查租户切块数、模型耗时、磁盘和并发；超出单机边界迁移存储 |
| 数据丢失 | 从一致性备份恢复，确认integrity_check和租户检索；生产需实测RPO/RTO |

证据复查保证在该次数据库校验时间点文档仍有效；响应网络发送后发生的删除无法撤回客户端已接收的数据。没有对外部系统和缓存承诺全局线性一致性。

## 8. 学习重点、难点与面试问题

对应书稿04/05/06/10/11/12/13/14章。建议先跑demo，再阅读store的事务边界，然后对照测试理解故障处理。

- 重点：区分检索证据和生成答案，保留文档id、版本与切块位置；RRF分数是排序融合分值，不能解释为相似概率。
- 难点：模型调用不能占用写事务，调用完成后仍要检查版本；删库与在途查询并发时必须明确返回语义。
- 面试：为什么不允许客户端指定tenant？因为认证身份才是权限来源；只在输出时过滤会让未授权文本进入模型上下文。
- 面试：为什么换embedding不能直接复用旧向量？维度一致也不代表向量空间一致，需要索引契约与全量重建。
- 面试：如何把此项目迁移到高可用？先建立容量基线，再拆摄取任务队列、迁移关系库与向量存储、引入事件对账，不能仅增加容器副本。
- 项目坑：离线哈希embedding不是语义模型；字符窗口不是token预算；远程embedding和生成成本应独立计量；当前没有成本计费与答案缓存。
- 上线验收：用本企业标注集评估Recall@k、MRR、拒答和答案支持度，补齐负载、故障注入、安全审计与恢复演练。本项目demo评估只有3项确定性验收，不替代真实质量评测。


## 9. 持久化异步摄取与运维（本次新增）

### 启动与调用

API与worker使用相同的模型、索引契约、KB_DB和身份环境；二者在同一台机器访问本机数据库。worker不随API启动，避免每个Web副本意外重复启动消费线程。

```powershell
# 终端一（先注入第1节所需环境）
python run.py serve
# 终端二（注入相同环境）
python run.py worker
# 运维或批处理：最多处理一个当前可认领任务，没有任务即退出
python run.py worker --once
```

```powershell
$headers = @{ Authorization = "Bearer $env:KB_CLIENT_KEY" }
$base = $env:KB_SERVICE_URL
$body = @{
    idempotency_key = 'travel-policy-change-20261105-01'
    doc_id = 'travel'
    title = '差旅制度'
    text = '差旅酒店报销上限为每晚600元。'
    expected_version = 0
} | ConvertTo-Json
$job = Invoke-RestMethod "$base/v1/jobs/ingest" -Method Post -Headers $headers -Body ([Text.Encoding]::UTF8.GetBytes($body)) -ContentType 'application/json'
Invoke-RestMethod "$base/v1/jobs/$($job.id)" -Headers $headers
# 需要取消时（已成功或失败的任务不能取消）
# Invoke-RestMethod "$base/v1/jobs/$($job.id)/cancel" -Method Post -Headers $headers
```

| 接口 | 行为 |
|---|---|
| POST `/v1/jobs/ingest` | writer/admin提交；202表示已持久化接受，不表示入库成功 |
| GET `/v1/jobs/{id}` | 当前租户读取状态、尝试次数、安全错误码和最终结果；不返回正文 |
| POST `/v1/jobs/{id}/cancel` | writer/admin取消queued/running任务；旧worker随后无法提交 |
| GET `/v1/documents/{id}` | 当前租户读取文档全文、版本；其他租户返回404 |
| GET `/v1/documents?limit=100&after=...` | 以文档ID升序游标分页，最多500条 |
| GET `/v1/audit?limit=100&before=...` | admin按审计ID倒序分页，最多500条 |
| GET `/v1/metrics` | admin读取当前租户文档数、切块数、各状态任务数 |

当页数恰好等于limit时可能返回游标，但下一页为空。列表跨多个请求不承诺快照一致性。详情接口延续租户授权，不提供文档级ACL。

### 状态机与一致性

任务路径：queued → running → succeeded；模型或存储暂时失败时重新queued，超过次数后failed；版本冲突或容量不足直接failed；queued/running可转cancelled。

- 幂等范围为租户+提交密钥摘要+idempotency_key。同键同参数返回原任务，同键不同参数409；轮换密钥后范围改变。终态重复提交不会自动重跑，业务决定重试时需新的幂等键和正确版本。
- BEGIN IMMEDIATE事务认领任务，单次只有一个worker得到有效租约；租约带随机token。续期每租约时长的1/3执行，向量调用不占数据库写事务。
- 崩溃后到期任务可重新认领，尝试次数递增；旧token失效。最终文档、切块、审计和succeeded状态在同一事务提交，避免文档已写但任务仍待处理。任务计算采用至少一次语义，外部模型调用可能重复计费。
- 取消先提交则旧worker无法入库；写入先提交则取消409。取消不能撤回已经发出的模型请求，正文在终态从任务payload清除，但数据库空闲页和备份不保证物理擦除。
- 失败重试等待min(60,2^attempts)秒，默认最多3次；不在Web请求中阻塞等待结果。所有worker停止后任务只保存在队列，不会自行处理。
- SIGINT/SIGTERM使worker完成当前任务后退出；部署终止宽限期应覆盖当前任务处理时间。强制终止后靠租约恢复。长时间停机应监测queued数量和最老任务时间，指标接口目前仅提供状态数量。

| 环境变量 | 默认值 | 用途 |
|---|---|---|
| KB_MAX_PENDING_JOBS | 100 | 每租户queued+running的背压上限 |
| KB_JOB_MAX_ATTEMPTS | 3 | 首次执行计入最大尝试次数 |
| KB_JOB_LEASE_SECONDS | 300 | 租约与崩溃恢复等待时间 |
| KB_MAX_CHUNKS | 5000 | 当前租户切块容量上限 |
| KB_MODEL_TIMEOUT | 25 | 单次远程请求超时秒数 |

任务终态保留用于幂等对账，不自动删除幂等记录；实际部署需制定任务元信息保留策略并评估磁盘增长。当前指标是租户授权JSON计数，不是Prometheus时序指标、延迟直方图或完整OpenTelemetry追踪。没有部署高可用调度器、SSO、外部向量库、文件解析、管理界面或分布式限流；这些能力不作为本次交付的已实现项。

### 版本防护与验收

旧实现删除文档后重建会重复使用版本1，导致旧证据可能误通过版本检查。本次document_versions保留每个文档历史最大版本，删除不清除墓碑；重建继续递增，旧引用与旧更新请求会冲突。历史已删除文档没有可恢复记录，因此升级前已有的在途请求应随旧服务一同排空。

当前18项自动化测试通过：包括8项新增任务/分页/版本测试及10项原有隔离、模型故障、并发和备份恢复测试。租约续期测试验证数据库续期与旧token拒绝，不声称完成长时间压力或真实进程强杀演练。远程模型仍使用模拟合约，Docker镜像、真实模型成本和现场吞吐未实测。运行测试不要求固定工作目录，备份测试使用绝对脚本定位。
