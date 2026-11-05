# 03.02 LlamaHub 连接器与增量同步

[返回全书目录 / Contents](../00-contents.md)

远程连接器把 API、数据库或协作文档转换成 Document。连接器目录帮助发现集成，但包名、鉴权方式和 load_data 参数需按具体版本确认。不要把教程中的动态加载示例当成长久稳定的生产依赖；生产代码应显式安装、导入并锁定经过测试的集成。

同步任务需要处理分页、速率限制、重试、游标、修改时间和删除事件。以 updated_at 为游标时，必须考虑同一时间戳多条记录和迟到更新。使用重叠时间窗加稳定 ID 去重，比单纯“严格大于上次时间”更稳健。只有所有页处理成功并持久化后，才能提交新的检查点。

读取权限不等于最终用户访问权限。一个服务账号能看到全公司文档，不代表所有用户都应检索这些文档。连接器应采集 ACL、来源版本和删除标记；下游在查询时重新执行授权。凭据最小化、日志脱敏与定期轮换属于同步设计的一部分。

## 重点与难点

重点：稳定 ID、检查点和删除传播。难点：至少一次同步下的幂等，以及半途失败后既不丢数据也不重复发布。

## 面试考点与参考回答

问：全量同步与增量同步如何配合？答：日常用增量减少成本，周期性全量对账发现漏删、权限漂移和游标缺口；对账结果应可审计。

## 项目中的坑与处置

坑：429 后立刻无限重试，引发雪崩并重复计费。处置：尊重 Retry-After，指数退避加抖动，限制尝试次数，对永久错误进入人工处理队列。

## 动手实验与验收

模拟三页数据，在第二页失败后重跑。验收：检查点不提前推进、稳定 ID 不重复、删除事件能清理旧节点和缓存。

## 代码实现补充：连接器结果的稳定 ID 与增量对账

依赖：Python 3.10+；仅使用 Python 标准库。

运行方式：将下面完整代码保存为独立 `.py` 文件，在独立进程执行 `python 文件名.py`；无需 API Key，不调用付费模型服务。成功时断言通过并打印结果。

```python
import hashlib
import json

def digest(row):
    # Include metadata: an ACL change also requires publication.
    payload = json.dumps(row, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()

def reconcile(snapshot, rows):
    ids = [r["source_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate source IDs")
    current = {r["source_id"]: digest(r) for r in rows}
    changed = [r for r in rows if snapshot.get(r["source_id"]) != current[r["source_id"]]]
    removed = sorted(set(snapshot) - set(current))
    return changed, removed, current

first = [{"source_id": "wiki:17", "text": "Limit 500", "tenant": "a"}]
changed, removed, snapshot = reconcile({}, first)
assert len(changed) == 1 and not removed
assert reconcile(snapshot, first)[0] == []
changed, removed, next_snapshot = reconcile(snapshot, [])
assert removed == ["wiki:17"]
print({"deleted": removed})
```

### 实现说明、验收与项目边界

把 LlamaHub 读取器的输出转换为此契约，再按 source_id 创建 Document。这里只接受完整、成功的快照；分页失败或仅返回一页时不能把缺失记录判为删除。先完成向量、关键词和缓存更新，最后提交 next_snapshot；真实存储需事务或可恢复检查点。
