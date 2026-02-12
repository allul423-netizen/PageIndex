# PageIndex3 模型迁移开发计划：OpenAI -> 硅基流动 DeepSeek V3

**日期:** 2026-02-12
**状态:** 待执行 (Pending)
**项目路径:** `D:\Antigravity\Pageindex3\`
**硅基流动API位置:** `D:\Antigravity\Pageindex3\.env`
**目标:** 将底层的 LLM 支持从 OpenAI (ChatGPT) 迁移至 硅基流动 (SiliconFlow) 的 DeepSeek V3 模型，并使用指定 PDF 进行功能验证。

---

## 1. 项目背景与分析

### 1.1 项目架构理解

**PageIndex3** 是一个**基于图谱的 RAG (Retrieval-Augmented Generation)** 框架。与传统的向量数据库 RAG 不同，它的核心机制是：

* **层级化索引 (Hierarchical Indexing):** 读取源文件（PDF, TXT, MD 等），将其切分并构建成一个树状或图状的知识结构。
* **推理式检索 (Reasoning Retrieval):** 在用户提问时，模型不依赖单纯的关键词匹配，而是像人类查阅目录一样，通过阅读高层摘要 -> 决策下一步路径 -> 深入阅读细节，来定位答案。
* **高 Token 消耗:** 构建索引和推理过程需要大量的 LLM 交互，因此成本和速度是关键瓶颈。

### 1.2 迁移原因与目标

* **当前状态:** 代码库默认配置为调用 OpenAI API (GPT-4o / GPT-3.5)。
* **痛点:** OpenAI 在处理大量文档索引时成本极高，且受限于网络环境。
* **解决方案:** 切换至 **硅基流动 (SiliconFlow)** 托管的 **DeepSeek V3**。
  * **成本优势:** 相比 GPT-4o，成本大幅降低。
  * **性能对标:** DeepSeek V3 在指令遵循和生成质量上对标 GPT-4o。
  * **兼容性:** 完全兼容 OpenAI SDK 格式，无需重构核心代码。

---

## 2. 实施方案 (第一阶段：DeepSeek V3)

此阶段的目标是**零代码逻辑修改**，仅通过配置变更完成迁移。

### 2.1 环境准备

* **工作目录:** `D:\Antigravity\Pageindex3\`
* **依赖检查:** 确保已安装必要的 Python 库 (需在终端运行):

    ```powershell
    cd D:\Antigravity\Pageindex3\
    pip install -r requirements.txt
    ```

### 2.2 配置文件修改

**目标:** 将 API 请求重定向到硅基流动的服务器。

* **操作文件:** 查找项目根目录下的 `.env` 文件（如果没有，则查找 `config.py` 或 `settings.py`）。
* **修改项:**

| 变量名 (Variable) | 旧值 (OpenAI) | **新值 (SiliconFlow / DeepSeek V3)** |
| :--- | :--- | :--- |
| `OPENAI_API_BASE` | `https://api.openai.com/v1` | **`https://api.siliconflow.cn/v1`** |
| `OPENAI_API_KEY` | `sk-proj-xxxx...` | **`sk-sf-xxxx...`** (请填入您的硅基流动 Key) |
| `MODEL_NAME` | `gpt-4o` | **`deepseek-ai/DeepSeek-V3`** |

### 2.3 代码微调 (Code Review)

虽然不需要重写逻辑，但需要检查以下参数以适配 DeepSeek V3：

1. **Temperature (温度):**
    * 推荐保持默认或设置在 `0.7` - `1.3` 之间。
2. **Timeout (超时):**
    * *关键点:* 由于我们要处理 PDF 索引，建议将 `timeout` 显式设置为 **120秒** 以上，防止大文件处理时连接中断。
3. **验证输出格式:**
    * DeepSeek V3 **不会** 输出 `<think>` 标签，无需添加清洗代码。

---

## 3. 测试与验证策略

在运行全量索引之前，必须进行连通性测试。

### 3.1 连接测试脚本

在 `D:\Antigravity\Pageindex3\` 下创建一个名为 `test_v3.py` 的文件，内容如下：

```python
from openai import OpenAI
import os

# 临时硬编码测试，确认通了之后再改配置文件
client = OpenAI(
    api_key="sk-sf-xxxxxxxx", # 替换您的 Key
    base_url="[https://api.siliconflow.cn/v1](https://api.siliconflow.cn/v1)"
)

print("正在测试 DeepSeek V3 连接...")
try:
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3",
        messages=[{"role": "user", "content": "你好，请回复'连接成功'"}],
        temperature=0.7
    )
    print("返回结果:", response.choices[0].message.content)
except Exception as e:
    print("错误:", e)
