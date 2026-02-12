# Pageindex 逻辑文档

本文档详细介绍了 `pageindex` 库的逻辑和文件处理流程，该库旨在从 PDF 和 Markdown 文档中提取层级结构（目录/TOC）。

## 1. 概述

`pageindex` 库提供了两个主要的文档处理入口点：

- **PDF 处理**：提取文本，检测/提取 TOC，映射页码，并构建层级 JSON 结构。
- **Markdown 处理**：解析 Markdown 标题，根据 token 数量对树进行瘦身，并生成摘要。

主要的入口点是 `run_pageindex.py`，它分发到 `page_index.page_index_main`（用于 PDF）或 `page_index.page_index_md.md_to_tree`（用于 Markdown）。

## 2. PDF 处理逻辑 (`page_index.py`)

PDF 处理流程较为复杂，涉及多个阶段，包括 OCR/文本提取、TOC 检测、TOC 提取、页面映射以及针对大章节的递归处理。

### 2.1. 初始化设置与文本提取

- **输入**：PDF 文件路径或 BytesIO 对象。
- **文本提取**：使用 `PyPDF2` 或 `PyMuPDF`（通过 `get_page_tokens` 函数）提取每一页的文本。
- **Token 计数**：使用 `tiktoken` 计算每一页的 token 数量。

### 2.2. 目录 (TOC) 检测

- **`check_toc`**：遍历文档开头（默认前 20 页）以查找 TOC。
- **`find_toc_pages`**：使用 LLM 检查页面是否包含 TOC (`toc_detector_single_page`)。在找到包含 TOC 的页面后，如果再遇到不含 TOC 的页面则停止。

### 2.3. 目录提取与解析

- **`toc_extractor`**：提取 TOC 页面的原始文本。
- **`toc_transformer`**：使用 LLM 将原始 TOC 文本转换为结构化的 JSON 格式（节点列表，包含 `structure`、`title` 和 `page`）。
- **`toc_index_extractor`**：如果 TOC 缺少页码，或者为了验证它们，该步骤尝试通过查看文档内容来查找章节的物理页面索引。

### 2.4. 页码映射与偏移量计算

- **`extract_matching_page_pairs`**：匹配 TOC 中找到的 `page` 号码（逻辑页码）与通过内容匹配找到的 `physical_index`（实际 PDF 页面索引）。
- **`calculate_page_offset`**：计算逻辑页码与物理页面索引之间的偏移量（例如，如果逻辑第 1 页是物理第 5 页，则偏移量为 4）。
- **`add_page_offset_to_toc_json`**：将此偏移量应用于所有节点，以获取它们的 `physical_index`。

### 2.5. 处理无 TOC 或无页码的情况

- **`process_no_toc`**：如果未找到 TOC，则对文档进行分块，并使用 LLM 生成 TOC 结构（`generate_toc_init` 和 `generate_toc_continue`）。
- **`process_toc_no_page_numbers`**：如果找到 TOC 但没有页码，则对文档进行分段，并使用 LLM 查找每个章节的起始位置（`add_page_number_to_toc`）。

### 2.6. 验证与修正 (`fix_incorrect_toc`)

- **`verify_toc`**：抽样检查 TOC 项目，以确保标题确实出现在引用的页面上（`check_title_appearance`）。
- **`fix_incorrect_toc`**：如果验证失败（准确率 < 100%），则尝试修复不正确的索引。
  - 识别上一个正确项目和下一个正确项目之间的范围。
  - 在该范围内搜索标题的确切起始页（使用 `single_toc_item_index_fixer`）。
  - 此过程最多重试 3 次（`fix_incorrect_toc_with_retries`）。

### 2.7. 递归处理 (`process_large_node_recursively`)

- 如果一个节点跨越太多页面（`max_page_num_each_node`）或包含太多 token（`max_token_num_each_node`），则将其视为子文档。
- 该函数在该节点的页面范围内递归调用 `meta_processor` 以进一步分解它。
- **`check_title_appearance_in_start_concurrent`**：验证子章节是否在其分配的页面开头开始。

### 2.8. 后处理

- **`post_processing`**：将扁平的节点列表转换为嵌套的树结构（`list_to_tree`）。
- **`add_preface_if_needed`**：如果第一章从第 1 页之后开始，则添加“前言 (Preface)”节点。
- **`validate_and_truncate_physical_indices`**：确保没有节点引用超出文档末尾的页面。

### 2.9. 最终输出生成

- **`write_node_id`**：为节点分配唯一 ID。
- **`add_node_text`**：（可选）向每个节点添加完整的文本内容。
- **`generate_summaries_for_structure`**：（可选）使用 LLM 为每个节点生成摘要。
- **`generate_doc_description`**：（可选）生成全局文档描述。

---

## 3. Markdown 处理逻辑 (`page_index_md.py`)

Markdown 处理通常更简单，因为结构是显式的。

### 3.1. 解析

- **`extract_nodes_from_markdown`**：基于正则表达式解析 Markdown 标题（`#`、`##` 等）以识别节点及其行号。
- **`extract_node_text_content`**：提取标题之间的文本内容。

### 3.2. 树结构构建与瘦身

- **`tree_thinning_for_index`**：将小节点（低于 `min_token_threshold`）合并到其父节点或兄弟节点中，以避免树过于细碎。
- **`build_tree_from_nodes`**：基于标题级别逻辑重建树。

### 3.3. 摘要生成

- **`generate_summaries_for_structure_md`**：如果请求，为节点生成摘要。
- **`format_structure`**：清理字段以进行最终输出。

---

## 4. PDF 处理流程图

```mermaid
flowchart TB
    Start([开始 PDF 处理]) --> ExtractText[提取文本 & 计数 Token]
    ExtractText --> CheckTOC{检查 TOC?}
    
    CheckTOC -- 是 --> TOCFound{找到 TOC?}
    CheckTOC -- 否 --> ProcessNoTOC[处理无 TOC\n(从内容生成结构)]
    
    TOCFound -- 否 --> ProcessNoTOC
    TOCFound -- 是 --> ExtractTOC[提取 TOC 内容]
    
    ExtractTOC --> CheckPageNums{TOC 含页码?}
    
    CheckPageNums -- 是 --> ProcessWithPageNums[带页码处理]
    CheckPageNums -- 否 --> ProcessNoPageNums[无页码处理]
    
    ProcessWithPageNums --> TransformTOC[转换 TOC 为 JSON]
    TransformTOC --> MapPages[映射逻辑页到物理页]
    MapPages --> Offset[计算页码偏移量]
    Offset --> ApplyOffset[应用偏移量到索引]
    
    ProcessNoPageNums --> TransformTOCNoPage[转换 TOC 为 JSON]
    TransformTOCNoPage --> SegmentDoc[分段文档]
    SegmentDoc --> FindStarts[通过 LLM 查找章节起始]
    
    ProcessNoTOC --> GenerateInit[生成初始结构]
    GenerateInit --> GenerateCont[生成后续结构]
    
    ApplyOffset --> VerifyTOC[验证 TOC 准确性]
    FindStarts --> VerifyTOC
    GenerateCont --> VerifyTOC
    
    VerifyTOC --> AccuracyCheck{准确率 > 阈值?}
    
    AccuracyCheck -- 是 --> FixIncorrect[修复不正确索引\n(迭代修正)]
    AccuracyCheck -- 否 --> Fallback{回退模式?}
    
    Fallback -- 转无页码模式 --> ProcessNoPageNums
    Fallback -- 转无 TOC 模式 --> ProcessNoTOC
    
    FixIncorrect --> RecursiveCheck{检查节点大小}
    VerifyTOC -- 完美 --> RecursiveCheck
    
    RecursiveCheck -- 太大 --> RecursiveProcess[递归处理\n(将节点视为子文档)]
    RecursiveProcess --> RecursiveCheck
    
    RecursiveCheck -- OK --> PostProcess[后处理\n(构建树，生成 ID)]
    
    PostProcess --> OptionalSteps{可选步骤?}
    
    OptionalSteps -- 摘要 --> GenSum[生成摘要]
    OptionalSteps -- 文本 --> AddText[添加节点文本]
    
    GenSum --> FinalOutput([最终输出 JSON])
    AddText --> FinalOutput
    OptionalSteps -- 无 --> FinalOutput
```

## 5. 详细函数逻辑 (关键组件)

### `fix_incorrect_toc` 逻辑

1. 识别 `verify_toc` 返回 "no" 的所有节点。
2. 对于每个不正确的节点：
    - 查找 `prev_correct`（最近的上一个正确节点的物理索引）。
    - 查找 `next_correct`（最近的下一个正确节点的物理索引）。
    - 提取 `prev_correct` 和 `next_correct` 之间的文本内容。
    - 使用 LLM (`single_toc_item_index_fixer`) 在此文本范围内查找标题的确切起始页。
    - 验证新索引。
3. 使用更正后的索引更新 TOC。
4. 如果错误仍然存在，则最多重复 3 次。

### `process_no_toc` 逻辑

1. 将文档分成块（页面组）。
2. `generate_toc_init`：从第一个块生成初始 JSON 结构。
3. `generate_toc_continue`：迭代地使用后续块更新结构，将新章节添加到现有树中。
4. 将匹配到的 `<physical_index_X>` 标签转换为整数页码。
