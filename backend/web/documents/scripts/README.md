# 文档索引构建脚本

`insert_documents.py` 用于把 `web/documents/data.txt` 切分并向量化，
写入 LanceDB 知识库（`web/documents/lancedb_storage`）。

**这是离线脚本，不参与线上请求流程**。只有在 `data.txt` 内容更新后才需要重新执行：

```bash
python -m web.documents.scripts.insert_documents
```

线上检索逻辑在 `web/views/friend/message/chat/graph.py`，它只读取已建好的索引。
