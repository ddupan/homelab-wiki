---
title: Marker 文档转换指南
lifecycle: unknown
evidence: documented
last_reviewed: 2026-09-16
last_verified: null
---

# Marker

Marker 用 GPU 将 PDF 转为 Markdown 等格式。本页依据 homelab-infra `apps/marker/README.md`、
Dockerfile 与 Kubernetes manifests，以及下列上游 API 源码整理，未查询运行环境。
源码 Deployment 仍使用 `<your-registry>/marker:latest` 占位符，不能据此认定服务已经上线。

## 使用前提与入口

先由维护者完成镜像构建、部署与可达性确认，再使用集群内入口
`http://marker.default.svc.cluster.local:8001`。所读配置没有记录外部域名或客户端认证流程。
普通应用无需重新执行 README 中的部署步骤。

镜像未固定 `marker-pdf` 版本，示例必须与实际部署的 `/docs` 接口说明核对。
上游当前 `marker_server` 默认绑定 `127.0.0.1`，而本地配置只传 `--port`；
如果所构建版本也如此，维护者需设置 `--host 0.0.0.0` 才能供 Service 访问。
这是部署前检查点，本轮未修改 manifest 或判定现场故障。

## 转换一个 PDF

在能访问该 Service 的客户端，准备一份适合测试的 `sample.pdf`，设置 `MARKER_BASE_URL`
为已确认的入口。上传会处理文件并占用 GPU，先以单个小文件串行验证：

```bash
curl --fail --silent --show-error \
  -F 'file=@sample.pdf;type=application/pdf' \
  -F 'output_format=markdown' \
  "${MARKER_BASE_URL:?请设置已确认的入口}/marker/upload" \
  -o marker-result.json
```

检查转换是否成功，再将 Markdown 保存到本地：

```python
import json
from pathlib import Path

result = json.loads(Path("marker-result.json").read_text())
if result.get("success") is not True:
    raise SystemExit("转换失败，请检查返回的 error 字段")
Path("sample.md").write_text(result["output"])
```

接口和返回结构依据 [Marker server 源码](https://github.com/datalab-to/marker/blob/master/marker/scripts/server.py)。
HTTP 成功不等于转换成功，需要检查 `success`。返回还可能包含图片数据；仅写出 `output`
不会将图片自动保存为独立附件。需要完整图文时应按实际版本返回的图片字段另行保存并核对引用。

## 资源与文档边界

本地 README 的目标是适配 4 GB 显存，保持单副本、单 worker，并避免并发转换。
显存不足时先缩小测试文件或处理范围，不直接增加副本或并发。
Pod 没有业务 PVC，消费者应保存转换结果，不能将容器临时目录当文档库。

转换结果需要复核表格、代码、顺序及遗漏，再写入知识库；转换工具不确认文档事实或当前服务状态。
连接失败检查部署入口与监听地址，转换失败检查文件、模型加载及 GPU 资源。
依赖为 Kubernetes、GPU 设备支持、模型与临时磁盘；部署维护入口为 `apps/marker/README.md`。
