<!-- Exported from Claude Docs on 2026-11-27. -->

# Investment Decision Memo v4：远离训练数据的检验之后

2026-11-27 · Dekun Sun

结论：预登记的“远离训练数据的稳定性检验”两个阶段都成立，所以更大规模的晶体筛选从暂缓改为候选投入，先做一个小规模、从初始结构出发的试点；电池维持两笔内部小投入和限定范围的合作；芯片散热维持观察。

## 结论：三笔候选投入

这份备忘录接替 v3（2026-11-24）。v3 之后的新证据是外推检验的两个阶段：第一阶段在 WBM 上（11-24），第二阶段在外部数据库 Alexandria 上（11-27）。依据是三个技术模块、两次商业证据关卡和看板里的 50 条证据。

| 候选投入 | 决定 | 为什么 | 先做的小步骤 |
| --- | --- | --- | --- |
| 更大规模的晶体筛选 | 候选投入（v3：暂缓） | 只用 MP 数据训练的模型，在结构类型 MP 里没有、化学体系熟悉的候选上，挑稳定结构的能力和熟悉的候选上相近：第一阶段比值 0.91（事后修正后；预登记为 0.94），第二阶段 0.97。但第一阶段修正后的 95% 区间下限和第二阶段的下限都只是刚过 0.8；第二阶段从 DFT 弛豫好的结构出发；第二阶段里化学和结构同时陌生时开始下降 | 一个小试点：从初始结构出发、化学和结构同时陌生的候选，用表现最好的模型；先写设计和花费上限，再决定花不花算力 |
| 更完善的芯片散热工程测试 | 观察 | 问题是真的，验收指标也已知（OCP 冷板热阻）；但买家一侧的一手来源都指向冷却架构，没有一家说材料是限制 | 如果走“自己采用”路径，一个便宜的下一步是问自己的封装团队：热阻里哪一层最大、材料能不能改变它（推断） |
| 新的固态电解质实验合作 | 批准（限定范围） | 电池关卡找到了买家侧的电芯级指标（大众：700 次循环、容量损失不超过 20%，没写测试条件；USABC 的电芯目标）。买家点名的材料限制是界面耐久性，不是电导率；没有买家侧的电导率门槛 | 只谈联合探索，里程碑按带测试条件（温度、倍率）的电芯级指标设。两笔内部小投入（整理已有实测数据、进入新家族时先做一小组探索性样本）保留 |

“候选投入”的意思是：证据支持把它列进候选，但还不够批准。这是一份练习备忘录，只用公开数据，所有建议都是推断，不代表 DeepMind 的计划。

## 1. 新证据：远离训练数据的稳定性检验

模型在陌生结构类型上挑稳定结构的能力，是熟悉候选的 0.91（WBM，事后修正后；预登记为 0.94）和 0.97（Alexandria）倍；按事先写好的规则，两个阶段都是“成立”。

**要回答的问题。** v3 说，“AI 能发现新结构”在已知原型附近有证据，离开已知原型就没有。这次问：只用 MP 数据训练的模型，能不能在离训练数据很远的候选里可靠地认出热力学稳定的结构。

**设计。**

- 把“远”分成两类：化学体系是否在 MP 里出现过，结构类型（框架）是否在 MP 里出现过。得到四个格子：插值（都熟悉）、化学外推、结构外推、双重外推。
- 指标是比值 r = 外推格的得分 / 插值格的得分。结构外推格决定看板的 D10。
- 判定规则（r 的门槛两个阶段相同）：r 的 95% 区间下限 ≥ 0.8 且模型明显好于基线 → 成立；区间上限 < 0.5 → 失败；其他 → 部分成立。“好于基线”的检验不同：第一阶段要比 Wrenformer 高出 0.10 以上；第二阶段只要求 Somers' D > 0.2，只和随机比。两个阶段的规则和代码（第二阶段还有样本）都在打分前推到公开仓库（`ffdb574`、`c3f5fd2`）。

|  | 第一阶段：WBM | 第二阶段：Alexandria |
| --- | --- | --- |
| 候选从哪里来 | Matbench Discovery 的测试集，全部由元素替换生成 | 外部数据库，578 万个结构，来源多样 |
| 模型 | 前 10 名 MP-only 模型（只重新计分） | CHGNet、MACE-MP-0、SevenNet-0、MatRIS-10M-MP（在本机重新弛豫 1,800 个结构） |
| 结构外推格里含稳定结构的框架 | 30（事后修正后） | 90（样本里）；全量 324 |
| 结构外推 r（95% 区间） | 0.94（0.87–1.04）；事后修正后 0.91（0.81–1.03） | 0.97（0.80–1.19） |
| 双重外推 | 成立（1.17；修正后 1.18） | 部分成立（0.91；去掉两个预筛来源后 0.72） |
| 和基线比 | 只看组成和原型的 Wrenformer 明显下降（r 0.58；修正后 0.46） | 没有模板式基线，只和随机比：结构外推格 Somers' D 中位数 0.58（门槛 0.2） |
| 预登记的判定 | 成立 | 成立；去掉 m3gnet、orbital 两个预筛来源后也成立（0.95，0.83–1.14） |

**它说明了什么。**

- 结构类型陌生、化学体系熟悉时，这些模型基本保住了挑稳定结构的能力；结构外推格里含稳定结构的框架，第二阶段样本有 90 个，第一阶段（修正后）有 30 个。
- 第二阶段里，“远”的代价主要出现在化学和结构同时陌生时（第一阶段温和的双重外推格没有下降）：双重外推格里，MACE-MP-0 和 SevenNet-0 的能量误差约是插值格的 1.5 倍。
- 模型之间的差别比格子之间的差别大：每个格子里 Somers' D 都从 CHGNet（各格 0.26–0.35）排到 MatRIS-10M-MP（各格 0.76–0.82）。在这个样本里，选哪个模型比“离训练数据多远”影响更大。

**它没有说明什么。**

- 从零开始的发现能力：第二阶段从 DFT 弛豫好的结构出发，预测里含有 DFT 真值，只衡量误差是否小于离凸包的距离。
- 生成模型能否产生远离已知原型的结构：CSP 对照（E048）的结论没有变。这次检验的是筛选（给定候选、挑稳定的），不是生成。
- 含 Co、Cr、Fe、Mn、Mo、Ni、V、W 的氧化物和氟化物（GGA+U 体系）：第二阶段排除了这些体系。
- 差距很大时的稳健性：第一阶段修正后的下限（0.81）和第二阶段的下限（0.80）都只是刚过 0.8。

**对决策的含义。** v3 的触发条件是“离已知原型更远的测试集上，模型仍有区分和增量价值”。两个阶段都满足了预登记的规则（都成立），但第二阶段的“增量价值”只和随机比过。所以更大规模的晶体筛选改为候选投入。不直接批准，是因为还没有从初始结构出发的证据，而第二阶段的双重外推格已经开始下降。详见 `results/csp_far_stage1_20261124T0908Z/report.md` 和 `results/csp_far_stage2_20261125T1725Z/report.md`。

## 2. 科学证据和买家需求

三个模块都按同一套标准做：设计在运行前登记；基线包括领域经验规则或老一代模型，不只是随机；事后分析单独标明；设计或结果请独立代理审查并改正（外推检验审查的是设计）。两个重新计分的模块都和官方排行榜逐个对上。

| 模块 | 做了什么 | 证明了什么 | 没有证明什么 |
| --- | --- | --- | --- |
| 固态电解质 | OBELiX 499 个实测组成当离线实验室，比较六种选材策略 | 已知家族里，先验实测数据省下的实验远多于算法差别；但把同一掺杂系列整个留出后，机器学习只比“先测硫化物”的规则多省 3–4 次 | 跨家族迁移是否可靠（硫化物有效、氧化物无效）；强化学习是否有稳定优势（每个划分只训练了一个策略） |
| 芯片散热 | 62 个模型的 κ_SRME 重新计分；经验规则基线；7 个材料的实测对照 | 在 103 个简单二元化合物上，较好的模型对高导热候选的排序几乎一致；规则漏掉 BAs，模型没有 | 真实发现问题已解决（测试集太容易）；DFT 接近实测（7 个里 6 个低 10–27%）；已知材料能装进器件 |
| 稳定性筛选与 CSP | 73 个模型在 WBM（215,488 个候选）上重新计分；审计一篇 CSP 基准论文并重训 EquiCSP 7 次，做随机移除对照；远离训练数据的两阶段检验（WBM 重新计分；Alexandria 上用 4 个模型重新弛豫 1,800 个结构） | 小预算下大多数模型都挑得准（1% 预算：48 个模型 ≥ 95% 稳定，随机 15.5%）；超出“有把握”的候选后，前列模型约 90% 对，CHGNet 39%；生成模型对 1:1:2:6 目标的恢复依赖训练集里的钙钛矿框架；筛选模型在陌生结构类型上保住了挑稳定结构的能力（第 1 节） | 生成模型能产生离已知原型更远的结构；从初始结构出发时筛选是否同样稳健；对生成器做势函数优化是否安全；DFT 稳定的结构能不能合成 |

**三个模块合起来的形状（假设，未整体检验）：** 在容易的部分，模型已经和计算参考对得很好，剩下的不确定都在边缘。CSP 模块现在有两个经过预登记的点，而且方向不同：生成模型离开训练集里的原型就明显下降；筛选模型在陌生结构类型上基本保住，第二阶段里化学和结构同时陌生时才开始下降（第一阶段温和的双重外推格没有下降）。“边缘”在哪里，取决于任务是生成还是筛选。其他两个模块的“边缘”还没有这样的对照。

| 方向 | 需求侧证据 | 状态 |
| --- | --- | --- |
| 芯片散热 | 商业证据关卡（事先定好四个问题、只认一手来源、30 次检索内）：谁有问题、问题多大、怎么验收都有一手依据；“为什么需要新材料”没有 | 关卡跑完；方向降为观察 |
| 固态电解质 | 同格式的关卡（规则在检索前提交到 git，commit `80f062e`）：Q1–Q3 过，Q3 有保留（大众的 700 次循环目标没写测试条件）；Q4 过，但买家点名的材料限制是界面耐久性（丰田），买家一侧也点名了制造（大众）；没有买家侧的电导率门槛 | 关卡跑完；合作改为批准（限定范围） |
| 稳定性筛选与 CSP | 不是一个市场，而是所有方向都依赖的能力；需求要看它服务的方向 | 不适用 |
| 超导、聚变软件、二维材料 | 只有市场层的少数一手证据（例如 CFS 向 Fujikura 订购超过 1 万公里带材），没有技术模块 | 未评估 |

两次关卡指向同一件事：买家卡住的地方不在本项目回测的那一步。散热的买家指向冷却架构，而不是新材料；电池的买家指向界面耐久性和制造，而不是电导率。所有来源在 `data/thermal/literature_sources.csv` 和 `data/battery/literature_sources.csv`。

## 3. 投资组合：近期只批准便宜、能快速检验的投入

近期商业影响和长期科学价值分开列，不合成一个总分；没有成本数据，不写投资回报率。这两张表和看板的 `data/board/decisions.csv` 一致。

**近期商业影响**

| 投入 | 决定 | 卡住的资源 | 继续条件 | 停止条件 |
| --- | --- | --- | --- | --- |
| 电池：整理已有实测电导率数据 | 批准 | 数据 | 加入新数据后，按系列留出的回测仍优于家族规则，且区间不再重叠 | 按系列留出时仍和家族规则分不出来 |
| 电池：进入新家族时先做一小组探索性样本 | 批准（限定范围） | 实验 | 前几次实验里模型排序和实测一致 | 排序不一致：退回家族规则或随机探索 |
| 电池：用强化学习选材 | 暂缓 | 算力 | 多种子重做后，在官方、cv5 和按系列分组上都优于计算筛选 | 任一划分上不优于计算筛选 |
| 电池：和电池厂谈合作（只谈联合探索） | 批准（限定范围） | 伙伴 | 伙伴同意按带测试条件（温度、倍率）的电芯级指标设里程碑 | 没有伙伴愿意确定电芯级测试条件，或谈判要求超出电导率证据的承诺 |
| CSP：更大规模的晶体筛选算力 | **候选投入**（v3：暂缓） | 算力 | 从初始结构出发的小试点里，模型在化学和结构同时陌生的候选上仍有区分 | 试点里的区分接近随机，或和模板式基线一样失败 |
| 散热：为找导热材料提升通用模型的 κ 分数 | 不投入 | 算力 | 在更难、含复杂结构的数据集上，模型排序分歧变大 | — |
| 散热：发现新的导热材料 | 观察 | 算力和实验 | 一个买家（不是供应商）公开说某种材料是限制并愿意付钱 | — |
| 散热：已知高导热材料的器件化（即更完善的工程测试） | 观察 | 伙伴 | 金刚石散热服务器有按 OCP 热阻或结温报告的独立测试 | — |

另有一项假设，不是决定：为 DFT 稳定的头部候选找合成与结构确认伙伴。前提是一次文献回测显示，DFT 稳定的预测有可观比例被合成出来。

**长期科学价值**

| 投入 | 决定 | 卡住的资源 | 继续条件 | 停止条件 |
| --- | --- | --- | --- | --- |
| CSP：补做随机移除对照和多种子重训 | 完成：原型依赖成立（2026-11-24） | 算力（小，约 $19） | 已满足：对照后原型依赖仍成立，下一步在离已知原型更远处测试生成模型 | 没有出现：同等规模随机移除下下降没有消失，G0 也复现了论文两组的 consensus |
| 散热：热导率参考计算的物理（四声子、缺陷） | 暂缓 | 算力 | 散热回到优先时再启动 | — |

远离训练数据的两阶段检验只在本机跑，没有花钱，所以不单列一行；它的结果是上表 CSP 行的依据（看板 E049、E050）。

## 4. 与 v3 相比改了什么

- **更大规模的晶体筛选：暂缓 → 候选投入。** 依据是外推检验两个阶段都成立（E049、E050）。继续和停止条件改为看从初始结构出发的小试点。
- **第一阶段的一处事后修正。** 跑完后发现“结构类型是否见过”的标签有缺陷，398 个结构其实是已知框架。修正后结构外推的比值从 0.94 降到 0.91，仍成立。预登记的原结果没有改，修正单独写明。
- **第二阶段的偏离。** 一个 160 原子的结构在 MatRIS-10M-MP 上两次内存不足，按规则记为失败；去掉它结论不变（下限 0.81）。运行中断一次后从断点续跑；为此加的选项只影响运行顺序。
- **电池和散热的决定没有变。**
- **看板证据从 48 条增到 50 条。** 新增 E049（第一阶段）和 E050（第二阶段）。
- **v3 保留作为记录。**

## 5. 什么信息会改变这份建议

| 如果出现 | 会改变什么 |
| --- | --- |
| 从初始结构出发的小试点里，模型在化学和结构同时陌生的候选上仍有区分 | 晶体筛选从候选投入改为批准（限定范围） |
| 试点里的区分接近随机，或和模板式基线一样失败 | 晶体筛选退回暂缓；“模型能在陌生结构上筛选”只在从 DFT 结构出发时成立 |
| ABC2D6 组补训练两个种子后，不丢模板时 consensus 的波动也很大 | CSP 对照的解读要重新看；目前三个随机组都是 8，波动看起来不大 |
| 一个买家（不是供应商）公开说某种散热材料是限制并愿意付钱；或封装团队说热阻主要在材料层 | 散热从观察回到候选投入，先做已知材料的器件化 |
| 多种子重做后，强化学习在所有划分上稳定优于计算筛选 | 强化学习选材改为小规模试点 |
| 没有电池厂愿意确定电芯级测试条件 | 合作停止；两笔内部小投入保留 |

**下一步（按依赖关系，不按日历）：**

1. 晶体筛选的小试点：从初始结构（不是 DFT 弛豫好的结构）出发，重点是化学和结构同时陌生的候选，加一个模板式基线。先写设计和花费上限，再决定花不花算力。
2. 可选：ABC2D6 组补训练 seed 43、44（约 $5，付费，需要单独批准）。
3. 电池的强化学习多种子重做。
4. 看板 v0.2：排序和敏感度页、资源视图。

**局限：**

- 两个重新计分的模块和外推检验，真值都是 DFT，不是合成或实测。
- 外推检验：第一阶段修正后的下限和第二阶段的下限都只是刚过 0.8；第二阶段从 DFT 弛豫好的结构出发、没有模板式基线、排除了 GGA+U 体系（含 Co、Cr、Fe、Mn、Mo、Ni、V、W 的氧化物和氟化物），结构外推格的稳定结构多来自机器学习预筛的来源。
- CSP 对照只有 11 个目标、一个模型（EquiCSP）、一个家族，每组 3 次训练；ORB-v3 的模型版本是推断的。
- 离线的“实验次数”和“验证预算”都把每次验证当成一样贵；除了 CSP 对照的 GPU 花费，没有任何一笔投入的真实成本。
- 两次商业证据关卡各用了 28 次检索，只回答四个事先定好的问题。
- 市场层的很多数字来自系列文章，还没核实，看板里用灰色标出。
- 三种角色视角（科学验证、商业策略、S&O）用来组织问题，不代表任何人的意见。

**来源：** `modules/csp/FAR_FROM_TRAINING_TEST.md`、`modules/csp/FAR_FROM_TRAINING_STAGE2.md`、`results/csp_far_stage1_20261124T0908Z/report.md`、`results/csp_far_stage2_20261125T1725Z/report.md`、`modules/csp/RANDOM_REMOVAL_CONTROL.md`、`modules/csp/REPORT.md`、`modules/battery/REPORT.md`、`modules/battery/COMMERCIAL_EVIDENCE_GATE.md`、`modules/thermal/REPORT.md`、`modules/thermal/COMMERCIAL_EVIDENCE_GATE.md`、`data/board/`（看板数据）。仓库：[github.com/dekunsun/materials-intelligence](https://github.com/dekunsun/materials-intelligence)。上一版：[Investment Decision Memo v3](memo_v3.md)。

---

## English version

**Investment Decision Memo v4: after the far-from-training test**

2026-11-27 · Dekun Sun

Conclusion: both stages of the pre-registered stability test far from training data hold. So larger-scale crystal screening moves from defer to candidate investment, starting with a small pilot from initial structures. Batteries keep two small internal investments and a limited-scope partnership; chip cooling stays on watch.

## Conclusion: three candidate investments

This memo replaces v3 (2026-11-24). The new evidence since v3 is the two stages of the extrapolation test: Stage 1 on WBM (11-24) and Stage 2 on the external Alexandria database (11-27). It rests on three technical modules, two commercial evidence gates and 50 items of evidence on the board.

| Candidate investment | Decision | Why | First small step |
| --- | --- | --- | --- |
| Larger-scale crystal screening | Candidate investment (v3: defer) | MP-only models pick stable structures about as well on candidates whose framework is absent from MP (familiar chemistry) as on familiar ones: ratio 0.91 in Stage 1 (after a post-hoc fix; 0.94 as pre-registered), 0.97 in Stage 2. But Stage 1's corrected 95% lower bound and Stage 2's lower bound are both just above 0.8; Stage 2 starts from DFT-relaxed structures; and in Stage 2 performance starts to drop when chemistry and structure are both unfamiliar | A small pilot: start from initial structures, focus on candidates with unfamiliar chemistry and framework, use the best-performing model. Write the design and a spending cap first, then decide whether to spend compute |
| Fuller engineering tests for chip cooling | Watch | The problem is real and the acceptance metric is known (OCP cold-plate thermal resistance), but every first-hand buyer source points to cooling architecture; none says materials are the limit | If taking the "adopt it ourselves" path, a cheap next step is to ask our own packaging team which layer dominates thermal resistance and whether materials can change it (inference) |
| New solid-state electrolyte lab partnership | Approve (limited scope) | The battery gate found buyer-side cell-level metrics (VW: 700 cycles with at most 20% capacity loss, test conditions not stated; USABC cell targets). The material limit buyers name is interface durability, not conductivity; there is no buyer-side conductivity threshold | Joint exploration only, with milestones set on cell-level metrics with test conditions (temperature, rate). Keep the two small internal investments (curating existing measured data; a small exploratory batch when entering a new family) |

"Candidate investment" means the evidence supports putting it on the list, but not yet approving it. This is a practice memo using public data only; every recommendation is an inference and does not represent DeepMind's plans.

## 1. New evidence: the stability test far from training data

On unfamiliar frameworks, models pick stable structures 0.91 (WBM, after a post-hoc fix; 0.94 as pre-registered) and 0.97 (Alexandria) times as well as on familiar candidates; by the rules written in advance, both stages hold.

**The question.** v3 said that "AI can discover new structures" has evidence near known prototypes and none away from them. This test asks whether MP-only models can reliably identify thermodynamically stable structures among candidates far from their training data.

**Design.**

- "Far" is split two ways: whether the chemical system appears in MP, and whether the structure type (framework) appears in MP. This gives four cells: interpolation (both familiar), chemical extrapolation, structural extrapolation and double extrapolation.
- The metric is the ratio r = score in an extrapolation cell / score in interpolation. The structural-extrapolation cell decides D10 on the board.
- Rules (the same r thresholds in both stages): lower bound of the 95% interval of r ≥ 0.8 and models clearly better than the baseline → holds; upper bound < 0.5 → fails; otherwise → partial. The baseline test differs: Stage 1 requires beating Wrenformer by more than 0.10; Stage 2 requires only Somers' D > 0.2, against random. Both stages' rules and code (and Stage 2's sample) were pushed to the public repository before scoring (`ffdb574`, `c3f5fd2`).

|  | Stage 1: WBM | Stage 2: Alexandria |
| --- | --- | --- |
| Where candidates come from | Matbench Discovery's test set, all generated by element substitution | An external database of 5.78 million structures from many sources |
| Models | Top 10 MP-only models (re-scored only) | CHGNet, MACE-MP-0, SevenNet-0, MatRIS-10M-MP (1,800 structures relaxed again on a Mac) |
| Frameworks with a stable structure in the structural cell | 30 (after the post-hoc fix) | 90 (in the sample); 324 in the full pool |
| Structural r (95% interval) | 0.94 (0.87–1.04); 0.91 (0.81–1.03) after the post-hoc fix | 0.97 (0.80–1.19) |
| Double extrapolation | Holds (1.17; 1.18 after the fix) | Partial (0.91; 0.72 without two pre-screened sources) |
| Against a baseline | The composition-and-prototype baseline Wrenformer drops clearly (r 0.58; 0.46 after the fix) | No template-like baseline, only random: median Somers' D in the structural cell 0.58 (threshold 0.2) |
| Pre-registered outcome | Holds | Holds; also holds without the m3gnet and orbital pre-screened sources (0.95, 0.83–1.14) |

**What it shows.**

- With an unfamiliar framework but familiar chemistry, these models largely keep their ability to pick stable structures; frameworks with a stable structure in the structural cell number 90 in the Stage 2 sample, against 30 in Stage 1 (after the fix).
- In Stage 2, the cost of "far" appears mainly when chemistry and structure are unfamiliar together (Stage 1's mild double cell showed no drop): in the double cell, MACE-MP-0's and SevenNet-0's energy errors are about 1.5 times those in interpolation.
- Differences between models are larger than differences between cells: in every cell, Somers' D runs from CHGNet (0.26–0.35 across cells) to MatRIS-10M-MP (0.76–0.82). In this sample, the choice of model matters more than how far from training data the candidates are.

**What it does not show.**

- Discovery from scratch: Stage 2 starts from DFT-relaxed structures and its predictions contain the DFT truth, so it measures only whether the error is smaller than the distance to the hull.
- Whether generative models can produce structures far from known prototypes: the CSP control's conclusion (E048) is unchanged. This test is about screening (given candidates, pick the stable ones), not generation.
- Oxides and fluorides of Co, Cr, Fe, Mn, Mo, Ni, V and W (GGA+U systems): Stage 2 excluded these systems.
- Robustness with a wide margin: Stage 1's corrected lower bound (0.81) and Stage 2's (0.80) are only just above 0.8.

**What it means for decisions.** v3's trigger was "a test set further from known prototypes shows models still separate and add value there". Both stages meet the pre-registered rule for it (both hold), but in Stage 2 "add value" is shown only against random. So larger-scale crystal screening becomes a candidate investment. It is not approved outright because there is no evidence yet from initial structures, and Stage 2's double cell already starts to drop. See `results/csp_far_stage1_20261124T0908Z/report.md` and `results/csp_far_stage2_20261125T1725Z/report.md`.

## 2. Scientific evidence and buyer demand

All three modules follow the same standard: designs registered before running; baselines include domain rules of thumb or older models, not only random; post-hoc analyses marked separately; an independent agent reviews and corrects the design or the results (for the extrapolation test, the design). Both re-scoring modules match the official leaderboards value by value.

| Module | What was done | What it showed | What it did not show |
| --- | --- | --- | --- |
| Solid-state electrolytes | Used 499 measured OBELiX compositions as an offline lab and compared six selection policies | In known families, prior measured data saves far more experiments than the differences between algorithms; with whole doping series held out, ML saves only 3–4 more experiments than a "test sulfides first" rule | Whether transfer across families is reliable (works for sulfides, fails for oxides); whether RL has a stable advantage (one policy trained per split) |
| Chip cooling | Re-scored κ_SRME for 62 models; rule-of-thumb baseline; measured comparison for 7 materials | On 103 simple binaries, the better models rank high-conductivity candidates almost identically; the rule misses BAs, the models do not | That real discovery is solved (the test set is too easy); that DFT is close to measurement (6 of 7 are 10–27% low); that known materials fit into devices |
| Stability screening & CSP | Re-scored 73 models on WBM (215,488 candidates); audited a CSP benchmark paper and retrained EquiCSP 7 times for a random-removal control; two-stage test far from training data (WBM re-scored; 1,800 structures relaxed again with 4 models on Alexandria) | Most models pick well at small budgets (1% budget: 48 models ≥ 95% stable, random 15.5%); past the candidates a model is confident about, the top models are about 90% right, CHGNet 39%; the generative model's recovery of 1:1:2:6 targets depends on the perovskite frameworks in its training set; screening models keep their ability on unfamiliar frameworks (Section 1) | That generative models produce structures further from known prototypes; that screening is as robust from initial structures; whether optimising a generator against a potential is safe; that DFT-stable structures can be synthesised |

**The shape across the three modules (a hypothesis, not tested as a whole):** on the easy parts, models already agree well with the computed reference, and the remaining uncertainty sits at the edges. The CSP module now has two pre-registered points, and they point different ways: the generative model drops clearly away from its training prototypes, while screening models largely hold on unfamiliar frameworks and, in Stage 2, start to drop only when chemistry and structure are both unfamiliar (Stage 1's mild double cell showed no drop). Where the "edge" lies depends on whether the task is generation or screening. The other two modules have no such control at their edges yet.

| Direction | Demand-side evidence | Status |
| --- | --- | --- |
| Chip cooling | Commercial evidence gate (four questions fixed in advance, first-hand sources only, within 30 searches): who has the problem, how big, and how it is accepted all have first-hand support; "why a new material is needed" does not | Gate done; direction lowered to watch |
| Solid-state electrolytes | Gate in the same format (rules committed before searching, commit `80f062e`): Q1–Q3 pass, Q3 with a reservation (VW's 700-cycle target states no test conditions); Q4 passes, but the material limit buyers name is interface durability (Toyota), and a buyer also names manufacturing (VW); no buyer-side conductivity threshold | Gate done; partnership changed to approve (limited scope) |
| Stability screening & CSP | Not a market but a capability every direction relies on; demand depends on the direction it serves | Not applicable |
| Superconductors, fusion software, 2D materials | Only a few first-hand market-layer items (e.g., CFS ordering over 10,000 km of tape from Fujikura); no technical module | Not evaluated |

Both gates point to the same thing: buyers are stuck at a step other than the one this project back-tests. Cooling buyers point to cooling architecture, not new materials; battery buyers point to interface durability and manufacturing, not conductivity. All sources are in `data/thermal/literature_sources.csv` and `data/battery/literature_sources.csv`.

## 3. Portfolio: approve only cheap, quickly testable investments in the near term

Near-term commercial impact and long-term scientific value are listed separately, not combined into one score; with no cost data, no return on investment is given. Both tables match the board's `data/board/decisions.csv`.

**Near-term commercial impact**

| Investment | Decision | Binding resource | Continue if | Stop if |
| --- | --- | --- | --- | --- |
| Batteries: curate existing measured conductivity data | Approve | Data | With new data, the series-held-out back-test still beats the family rule and the intervals no longer overlap | Still indistinguishable from the family rule with series held out |
| Batteries: a small exploratory batch when entering a new family | Approve (limited scope) | Experiments | In the first few experiments the model's ranking agrees with measurement | Rankings disagree: fall back to the family rule or random exploration |
| Batteries: RL for material selection | Defer | Compute | After multi-seed reruns, beats computational screening on the official, cv5 and series-grouped splits | Does not beat computational screening on any split |
| Batteries: partnership talks with a cell maker (joint exploration only) | Approve (limited scope) | Partner | The partner agrees to milestones on cell-level metrics with test conditions (temperature, rate) | No partner will fix cell-level test conditions, or talks demand commitments beyond the conductivity evidence |
| CSP: larger-scale crystal screening compute | **Candidate investment** (v3: defer) | Compute | In a small pilot starting from initial structures, models still separate stable candidates where chemistry and framework are both unfamiliar | In the pilot, separation is close to random, or fails as badly as a template-like baseline |
| Cooling: raise general models' κ scores to find conductive materials | Do not fund | Compute | On a harder dataset with complex structures, model rankings diverge more | — |
| Cooling: discover new thermally conductive materials | Watch | Compute and experiments | A buyer (not a supplier) publicly says a material is the limit and will pay | — |
| Cooling: device integration of known high-conductivity materials (the fuller engineering tests) | Watch | Partner | Diamond-cooled servers get independent tests reported as OCP thermal resistance or junction temperature | — |

One hypothesis, not a decision: find synthesis and structure-confirmation partners for top DFT-stable candidates. It presupposes a literature back-test showing that a sizeable share of DFT-stable predictions have been synthesised.

**Long-term scientific value**

| Investment | Decision | Binding resource | Continue if | Stop if |
| --- | --- | --- | --- | --- |
| CSP: the random-removal control and multi-seed retraining | Done: prototype dependence held (2026-11-24) | Compute (small, about $19) | Met: prototype dependence survives the control; next, test generators further from known prototypes | Did not occur: the drop did not vanish under size-matched random removal, and G0 reproduced the paper's two arms |
| Cooling: physics of the reference κ calculation (four-phonon, defects) | Defer | Compute | Start when cooling is a priority again | — |

The two-stage test far from training data ran only on a local machine at no cost, so it has no row of its own; its results are the basis of the CSP row above (board E049, E050).

## 4. What changed since v3

- **Larger-scale crystal screening: defer → candidate investment.** Based on both stages of the extrapolation test holding (E049, E050). The continue and stop conditions now refer to a small pilot from initial structures.
- **A post-hoc correction in Stage 1.** After the run, the label for "framework seen before" turned out to be flawed; 398 structures were in fact known frameworks. After the fix, the structural ratio fell from 0.94 to 0.91 and still holds. The pre-registered result was not changed; the correction is reported separately.
- **Deviations in Stage 2.** One 160-atom structure ran out of memory twice on MatRIS-10M-MP and counts as a failure by the rule; without it the conclusion is unchanged (lower bound 0.81). The run was interrupted once and resumed from where it stopped; the option added for this only changes the order of the run.
- **Battery and cooling decisions are unchanged.**
- **Board evidence grew from 48 to 50 items.** New: E049 (Stage 1) and E050 (Stage 2).
- **v3 is kept as a record.**

## 5. What would change this recommendation

| If this happens | What changes |
| --- | --- |
| In a small pilot from initial structures, models still separate candidates with unfamiliar chemistry and framework | Crystal screening moves from candidate investment to approve (limited scope) |
| In the pilot, separation is close to random, or fails as badly as a template-like baseline | Crystal screening goes back to defer; "models can screen unfamiliar frameworks" holds only when starting from DFT structures |
| After two more ABC2D6 seeds, consensus without losing templates also varies widely | The CSP control's reading needs another look; the three random arms are all 8 now, so variation looks small |
| A buyer (not a supplier) publicly says a cooling material is the limit and will pay; or the packaging team says thermal resistance sits mainly in the material layer | Cooling goes from watch back to candidate investment, starting with device integration of known materials |
| After multi-seed reruns, RL beats computational screening on every split | RL for material selection becomes a small pilot |
| No cell maker will fix cell-level test conditions | The partnership stops; the two small internal investments stay |

**Next steps (by dependency, not by calendar):**

1. A small crystal-screening pilot: start from initial structures (not DFT-relaxed ones), focus on candidates with unfamiliar chemistry and framework, and add a template-like baseline. Write the design and a spending cap first, then decide whether to spend compute.
2. Optional: two more ABC2D6 seeds, 43 and 44 (about $5, paid, needs separate approval).
3. Multi-seed reruns of RL for batteries.
4. Board v0.2: ranking and sensitivity page, resource view.

**Limits:**

- In the two re-scoring modules and the extrapolation test, the truth is DFT, not synthesis or measurement.
- Extrapolation test: Stage 1's corrected lower bound and Stage 2's are only just above 0.8; Stage 2 starts from DFT-relaxed structures, has no template-like baseline, excludes GGA+U systems (oxides and fluorides of Co, Cr, Fe, Mn, Mo, Ni, V, W), and most stable structures in its structural cell come from ML pre-screened sources.
- The CSP control has only 11 targets, one model (EquiCSP), one family and 3 training runs per arm; the ORB-v3 model version is inferred.
- Offline "experiment counts" and "validation budgets" treat every validation as equally costly; apart from the CSP control's GPU spend, no investment has a real cost.
- Each commercial evidence gate used 28 searches and answers only four questions fixed in advance.
- Many market-layer numbers come from the essay series and are not yet verified; the board marks them in grey.
- The three role perspectives (scientific validation, commercial strategy, S&O) organise the questions and do not represent anyone's views.

**Sources:** `modules/csp/FAR_FROM_TRAINING_TEST.md`, `modules/csp/FAR_FROM_TRAINING_STAGE2.md`, `results/csp_far_stage1_20261124T0908Z/report.md`, `results/csp_far_stage2_20261125T1725Z/report.md`, `modules/csp/RANDOM_REMOVAL_CONTROL.md`, `modules/csp/REPORT.md`, `modules/battery/REPORT.md`, `modules/battery/COMMERCIAL_EVIDENCE_GATE.md`, `modules/thermal/REPORT.md`, `modules/thermal/COMMERCIAL_EVIDENCE_GATE.md`, `data/board/` (board data). Repository: [github.com/dekunsun/materials-intelligence](https://github.com/dekunsun/materials-intelligence). Previous version: [Investment Decision Memo v3](memo_v3.md).
