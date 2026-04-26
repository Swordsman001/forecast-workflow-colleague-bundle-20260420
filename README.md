# Forecast Workflow 交接 README

这份 README 是写给接手这套 workflow 的同事和同事使用的 AI 看的。目标只有一个：**让你在新的环境里能读懂、配置、运行、定位问题，并继续维护这套公共 workflow。**

---

## 1. 这是什么

这是一个面向非标准盈利预测模型的公共 workflow。它的核心目标是：

- 读取一个研究员维护的 Excel 盈利预测模型
- 理解 workbook 的结构和细分业务树
- 获取结构化财务事实
- 收集年报、纪要、研究资料、知识库、Alpha Pai 等文本证据
- 建立 workbook 细分结构和外部口径之间的映射
- 做预测逻辑审查
- 在满足条件时回写 candidate workbook

这套目录里的核心不是 `.md` 文档，而是 `runtime/` 下的 Python 脚本。  
`skills/` 主要是流程约束、设计意图、agent 说明，方便人和 AI 理解这套系统如何工作。

---

## 2. 目录结构

你现在拿到的目录里，最重要的是这些：

- `runtime/forecast_rollforward.py`
  公共 CLI 入口。大多数运行都从这里开始。

- `runtime/forecast_tools/rollforward.py`
  主流程核心逻辑。包括 workbook 结构识别、evidence 收集、mapping、reconciliation、forecast architecture、logic review、resume execution 等。

- `runtime/data_sources/tushare_client.py`
  Tushare API 封装。

- `runtime/data_sources/tushare_financial_facts.py`
  从 Tushare 获取结构化财务事实，并转成 workflow 内部使用的 contract。

- `runtime/forecast_tools/providers.py`
  外部文本证据 provider，包括 reference files、local KB、Alpha Pai。

- `runtime/wiki_query.py`
  本地知识库查询。

- `runtime/requirements.txt`
  Python 依赖。

- `skills/nonstandard-forecast-rollforward/SKILL.md`
  整套 workflow 的设计意图和主要步骤。

- `tests/`
  相关回归测试。

---

## 3. 这套系统当前的产品原则

这套 workflow 当前按下面的原则设计：

- `workbook 优先`
  先保留研究员原始 workbook 的细分表达，而不是强行把模型改造成官方披露格式。

- `稳定性优先`
  宁可停止并输出诊断，也不要假成功。

- `半自动执行`
  大部分步骤自动完成；少数高风险歧义点以候选决策包的形式交给人选择。

- `可回溯`
  每次运行都会尽量留下 facts、mapping、audit、run log、failure diagnostics 等工件。

---

## 4. 运行前必须配置的东西

### 4.1 Python 环境

先安装：

- `runtime/requirements.txt`

推荐先在独立虚拟环境里执行。

### 4.2 Tushare

这是结构化财务事实的主要来源。

你必须准备：

- `TUSHARE_TOKEN`

相关文件：

- `runtime/config.env.template`
- `runtime/data_sources/tushare_client.py`
- `runtime/data_sources/tushare_financial_facts.py`

如果你换环境，第一件事就是确认 `TUSHARE_TOKEN` 能被 `tushare_client.py` 读到。

### 4.3 Alpha Pai

相关文件：

- `runtime/forecast_tools/providers.py`

这里最可能存在环境耦合。你需要检查：

- Alpha Pai client 的导入方式
- 是否依赖本地绝对路径
- 是否依赖某个机器上的私有插件目录

如果你环境不同，优先改这里。

### 4.4 Local KB

相关文件：

- `runtime/wiki_query.py`

这部分可能依赖：

- 本地 wiki 文档目录
- 本地 sqlite 或其他知识库文件

如果你的环境里没有这些资产，有两种处理方式：

1. 改成你自己的 KB 路径
2. 暂时把 Local KB 视为空源，让 workflow 只靠 reference files + Alpha Pai 运行

---

## 5. Cloud Code 和 Codex 的区别

你现在的执行环境是 **Cloud Code**，不是 Codex。

所以要区分两层：

### 5.1 真正可执行的运行时

这是必须迁移和维护的部分：

- `runtime/forecast_rollforward.py`
- `runtime/forecast_tools/*.py`
- `runtime/data_sources/*.py`

### 5.2 说明性和约束性文档

这是帮助你理解系统的部分：

- `skills/nonstandard-forecast-rollforward/*.md`

这些文档不是 Python runtime 的必要依赖，但它们能帮助 AI 或人理解：

- workflow 的步骤
- agent 应该输出什么
- artifacts 的 schema 和约束

简单说：

- 想让系统跑起来：看 `runtime/`
- 想搞懂它为什么这样设计：看 `skills/`

---

## 6. 一次完整运行大概会发生什么

标准流程大致如下：

1. 读取 workbook，建立 blueprint / segment tree
2. 从 Tushare 拉结构化财务事实
3. 收集 reference files、meeting notes、research report、local KB、Alpha Pai 等证据
4. 建立 segment mapping
5. 做 reconciliation audit
6. 如果通过，进入 forecast architecture
7. 做 logic review
8. 编译写表动作
9. 生成 candidate workbook
10. 做 verification / parity audit / run log

---

## 7. 如何运行

### 7.1 标准运行

从这里开始：

- `runtime/forecast_rollforward.py`

如果 mapping / reconciliation / logic review 都过了，它会继续生成：

- `candidate.xlsx`
- `run_log.md`
- 以及多份 JSON artifacts

### 7.2 候选决策运行

当系统无法自动决定某些映射策略时，会进入：

- `candidate_decision_required`

这时它会给出：

- `A`
- `B`
- `C`
- `R`

含义：

- `A/B/C`：三种可继续执行的理解方案
- `R`：取消本次继续执行，返回上游重新桥接

之后可以用两阶段方式继续：

- `--resume-from <上次输出目录>`
- `--apply-candidate A|B|C|R`

也就是说，这不是“重新从头跑”，而是“从上一次决策点继续”。

---

## 8. 当前系统里最常见的问题

### 8.1 环境问题

最常见，不是算法错，而是：

- Tushare token 没配置
- Alpha Pai provider 在新环境里导入失败
- Local KB 路径失效

### 8.2 workbook 结构识别问题

有些模型会把：

- 比例行
- 费用率行
- 其他展示行

误识别进 segment tree。出现这种情况时，后面的 mapping 和 reconciliation 都会被污染。

### 8.3 外部口径和 workbook 细分层级不同

这是这套系统的难点之一。

常见情况：

- Tushare 给的是粗口径
- workbook 拆得更细

这时会进入：

- `proxy`
- `residual`
- 或 `candidate_decision_required`

### 8.4 逻辑层 fail

即使 reconciliation 过了，也可能在 logic review 被拦住，比如：

- 增长路径过于爆炸
- year-specific tempo 不合理
- 明显没有足够锚点却继续预测

---

## 9. 接手顺序建议

不要一上来就改复杂逻辑，建议按这个顺序：

1. 先确认 Python 环境和依赖
2. 先配置 `TUSHARE_TOKEN`
3. 再修 Alpha Pai / Local KB provider
4. 跑最小测试
5. 跑一个真实 case
6. 最后再考虑继续泛化 mapping / bridge generation

---

## 10. 建议先跑的测试

优先跑这几个：

- `tests/test_tushare_client.py`
- `tests/test_tushare_financial_facts.py`
- `tests/test_forecast_rollforward.py`

如果这些都不过，不要急着跑真实 case。

---

## 11. 当前已知的通用性边界

这套 runtime 已经清理过旧案例业务模板，但你还是要知道：

- 它不是“只适用于豪威或沃尔核材”的脚本集合
- 但也还没达到“完全行业无关、完全无语义偏置”的理想状态

已经清理掉的包括：

- 旧的 `手机CIS / 汽车CIS` 等硬编码业务模板
- 线缆 / 电力 / 发泡线等旧案例专用 driver 预设

但仍需持续关注：

- segment tree 对新 workbook 的适应性
- bridge generation 对跨层口径映射的泛化能力
- provider 对不同机器环境的兼容性

---

## 12. 如果你要让 AI 帮你继续维护

可以直接把下面这些文件一起给 AI：

- `runtime/forecast_rollforward.py`
- `runtime/forecast_tools/rollforward.py`
- `runtime/data_sources/tushare_financial_facts.py`
- `runtime/forecast_tools/providers.py`
- `skills/nonstandard-forecast-rollforward/SKILL.md`
- 以及某次真实运行输出的：
  - `financial_facts.json`
  - `segment_mapping.json`
  - `reconciliation_audit.json`
  - `logic_review.json`
  - `run_log.md`

这样 AI 才能既看代码，也看真实 artifacts。

---

## 13. 最后一句话

如果你只记住一句话，就记这个：

> 先把环境和 provider 接通，再跑测试和真实 case；不要在 runtime 还没稳定之前，就急着改预测逻辑。
