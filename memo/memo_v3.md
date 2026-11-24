<!-- Exported from Claude Docs on 2026-11-24. -->

# Investment Decision Memo v3：原型依赖经对照成立之后

2026-11-24 · Dekun Sun

结论：CSP 的原型依赖在预登记的随机移除对照后仍然成立，所以更大规模的晶体筛选继续暂缓，下一笔小钱给离已知原型更远的测试集；电池维持两笔内部小投入和限定范围的合作；芯片散热维持观察。

## 结论：三笔候选投入

这份备忘录接替 v2（2026-11-21）。v2 之后有两项新证据：电池商业证据关卡（11-21）和 CSP 随机移除对照（11-24）。依据是三个技术模块、两次商业证据关卡和看板里的 48 条证据。

| 候选投入 | 决定 | 为什么 | 先做的小步骤 |
| --- | --- | --- | --- |
| 更大规模的晶体筛选 | 暂缓 | 在元素替换生成的候选上，1% 预算已有 48 个模型挑到至少 95% DFT 稳定的结构；多花算力买到的是更多同一分布的候选。CSP 对照显示，生成模型在这些目标上依赖训练集里的钙钛矿框架；离已知原型更远的地方仍没有证据 | 建一个离已知原型更远的测试集，看模型在那里是否仍有区分和增量价值。先写设计，再决定花不花算力 |
| 更完善的芯片散热工程测试 | 观察 | 问题是真的，验收指标也已知（OCP 冷板热阻）；但买家一侧的一手来源都指向冷却架构，没有一家说材料是限制 | 如果走“自己采用”路径，一个便宜的下一步是问自己的封装团队：热阻里哪一层最大、材料能不能改变它（推断） |
| 新的固态电解质实验合作 | 批准（限定范围） | 电池关卡找到了买家侧的电芯级指标（大众：700 次循环、容量损失不超过 20%，没写测试条件；USABC 的电芯目标）。买家点名的材料限制是界面耐久性，不是电导率；没有买家侧的电导率门槛 | 只谈联合探索，里程碑按带测试条件（温度、倍率）的电芯级指标设。两笔内部小投入（整理已有实测数据、进入新家族时先做一小组探索性样本）保留 |

这是一份练习备忘录，只用公开数据，所有建议都是推断，不代表 DeepMind 的计划。

## 1. 新证据：CSP 随机移除对照

去掉钙钛矿框架的那一组，consensus 是 3、4、4；随机去掉同样数量的那一组是 8、8、8。按事先写好的规则，结论是“模板特有”。

**要回答的问题。** Wei et al.（[arXiv:2609.26502](https://arxiv.org/abs/2609.26502) v2）去掉训练集里的钙钛矿框架后重训 EquiCSP，11 个 1:1:2:6 目标的 consensus 从 8 降到 3。论文没有回答：下降是因为去掉了特定的模板，还是只是因为训练数据变少了。

**设计（2026-11-21 在任何训练之前提交到 git）。**

- 两组都去掉 ABC2D6 家族。PEROV 组再去掉 1,268 个钙钛矿框架结构，R 组再随机去掉同样数量的其他结构。训练集一样大（24,317 个），配方、种子和打分都相同。
- 每组 3 个训练种子（42、43、44），每次 106,000 步，在 RunPod A5000 上从头训练。生成、ORB-v3 弛豫和打分在本机 CPU 上。
- 判定规则：每个 R 都高于每个 PEROV，且平均差 ≥ 3 → 模板特有；平均差 ≤ 1 → 数据量；其他 → 无法判断。判定脚本在任何 R 组结果出来之前 commit。

| 弛豫后 consensus（11 个目标） | seed 42 | seed 43 | seed 44 | 平均 |
| --- | --- | --- | --- | --- |
| PEROV：去掉钙钛矿框架 | 3 | 4 | 4 | 3.67 |
| R1–R3：随机去掉同样数量 | 8 | 8 | 8 | 8.00 |

- 差别集中在 5 个目标（mp-6231、mp-19093、mp-16307、mp-6603、mp-6389）：R 组基本都能恢复，PEROV 组三个种子一次也没有。
- 用未弛豫的结果再算一遍，结论相同；五组的训练集和验证集都不含目标，也不含和目标化学式相同的结构。
- GPU 花费约 $19（7 次完整训练加 2 次 1,000 步的测试；价格乘时长的估算，没有对账单）。

**它说明了什么。** 在这个设置下，PEROV 的下降不能用“数据变少”解释。模型对这些目标的恢复，依赖训练集里的钙钛矿框架结构。

**它没有说明什么。**

- 是框架里的哪些结构起作用，模型又是怎么用到它们的。
- 能不能推广到其他家族、其他模型或更大的测试集。
- 样本很小：每组 3 次训练，精确置换 p = 1/20，是 3 对 3 能得到的最小值，不参与判定。ABC2D6 组只训练了 1 次。ORB-v3 的模型版本是推断的，没有确认。

**对决策的含义。** “AI 能发现新结构”这个卖点，在已知原型附近有证据；离开已知原型就没有。所以更大规模的晶体筛选继续暂缓，下一笔小钱给离已知原型更远的测试集。详见 `results/csp_r_eval_20261124T0335Z/report.md` 和 `modules/csp/RANDOM_REMOVAL_CONTROL.md`。

## 2. 科学证据和买家需求

三个模块都按同一套标准做：设计在运行前登记；基线包括领域经验规则或老一代模型，不只是随机；事后分析单独标明；跑完后请独立代理审查并改正。两个重新计分的模块都和官方排行榜逐个对上。

| 模块 | 做了什么 | 证明了什么 | 没有证明什么 |
| --- | --- | --- | --- |
| 固态电解质 | OBELiX 499 个实测组成当离线实验室，比较六种选材策略 | 已知家族里，先验实测数据省下的实验远多于算法差别；但把同一掺杂系列整个留出后，机器学习只比“先测硫化物”的规则多省 3–4 次 | 跨家族迁移是否可靠（硫化物有效、氧化物无效）；强化学习是否有稳定优势（每个划分只训练了一个策略） |
| 芯片散热 | 62 个模型的 κ_SRME 重新计分；经验规则基线；7 个材料的实测对照 | 在 103 个简单二元化合物上，较好的模型对高导热候选的排序几乎一致；规则漏掉 BAs，模型没有 | 真实发现问题已解决（测试集太容易）；DFT 接近实测（7 个里 6 个低 10–27%）；已知材料能装进器件 |
| 稳定性筛选与 CSP | 73 个模型在 WBM（215,488 个候选）上重新计分，按“给定验证预算”来读；审计一篇 CSP 基准论文；从头重训 EquiCSP 7 次，做论文缺的随机移除对照 | 小预算下大多数模型都挑得准（1% 预算：48 个模型 ≥ 95% 稳定，随机 15.5%）；超出“有把握”的候选后，前列模型约 90% 对，CHGNet 39%；生成模型对 1:1:2:6 目标的恢复依赖训练集里的钙钛矿框架（第 1 节） | 生成模型能产生离已知原型更远的结构；对生成器做势函数优化是否安全；DFT 稳定的结构能不能合成 |

**三个模块合起来的形状（假设，未整体检验）：** 在容易的部分——同一掺杂系列内插值、简单二元化合物、小预算筛选——模型已经和计算参考对得很好，剩下的不确定都在边缘。CSP 对照是这个假设里第一个经过预登记对照的点：离开训练集里的原型，生成模型的恢复率明显下降。其他两个模块的“边缘”还没有这样的对照。

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
| CSP：更大规模的晶体筛选算力 | 暂缓 | 算力 | 离已知原型更远的测试集显示模型在那里仍有区分和增量价值 | 模型在那个测试集上和模板一样失败 |
| 散热：为找导热材料提升通用模型的 κ 分数 | 不投入 | 算力 | 在更难、含复杂结构的数据集上，模型排序分歧变大 | — |
| 散热：发现新的导热材料 | 观察 | 算力和实验 | 一个买家（不是供应商）公开说某种材料是限制并愿意付钱 | — |
| 散热：已知高导热材料的器件化（即更完善的工程测试） | 观察 | 伙伴 | 金刚石散热服务器有按 OCP 热阻或结温报告的独立测试 | — |

另有一项假设，不是决定：为 DFT 稳定的头部候选找合成与结构确认伙伴。前提是一次文献回测显示，DFT 稳定的预测有可观比例被合成出来。

**长期科学价值**

| 投入 | 决定 | 卡住的资源 | 继续条件 | 停止条件 |
| --- | --- | --- | --- | --- |
| CSP：补做随机移除对照和多种子重训 | 完成：原型依赖成立（2026-11-24） | 算力（小，约 $19） | 已满足：对照后原型依赖仍成立，下一步在离已知原型更远处测试生成模型 | 没有出现：同等规模随机移除下下降没有消失，G0 也复现了论文两组的 consensus |
| 散热：热导率参考计算的物理（四声子、缺陷） | 暂缓 | 算力 | 散热回到优先时再启动 | — |

## 4. 与 v2 相比改了什么

- **CSP 对照完成，结论是“模板特有”。** 长期价值表里这一项从批准（限定范围）改为完成；更大规模晶体筛选的暂缓理由更充分。
- **电池关卡的结果写进正文。** v2 用更新框记录：合作从暂缓改为批准（限定范围），继续和停止条件改按带测试条件的电芯级指标写。
- **散热的决定没有变。** 仍是观察。
- **看板证据从 40 条增到 48 条。** 新增的是电池关卡的一手来源、论文里 ABC2D6 对 PEROV 的配对比较，以及 CSP 对照的结果（E048）。
- **v2 保留作为记录。** 它的两个更新框已经写进本文。

## 5. 什么信息会改变这份建议

| 如果出现 | 会改变什么 |
| --- | --- |
| 离已知原型更远的测试集上，模型仍有区分和增量价值 | 更大规模的晶体筛选从暂缓改为候选投入 |
| 在那个测试集上，模型和模板一样失败 | 晶体筛选的算力不再作为候选；“AI 发现新结构”只在已知原型附近成立 |
| ABC2D6 组补训练两个种子后，不丢模板时 consensus 的波动也很大 | CSP 对照的解读要重新看；目前三个随机组都是 8，波动看起来不大 |
| 一个买家（不是供应商）公开说某种散热材料是限制并愿意付钱；或封装团队说热阻主要在材料层 | 散热从观察回到候选投入，先做已知材料的器件化 |
| 多种子重做后，强化学习在所有划分上稳定优于计算筛选 | 强化学习选材改为小规模试点 |
| 没有电池厂愿意确定电芯级测试条件 | 合作停止；两笔内部小投入保留 |

**下一步（按依赖关系，不按日历）：**

1. 离已知原型更远的稳定性测试集：先写设计，包括数据来源、和各模型训练集的泄漏、判定规则；设计通过后再决定花不花算力。
2. 可选：ABC2D6 组补训练 seed 43、44（约 $5，付费，需要单独批准），直接测不丢模板时的训练波动。不会改变这次的判定。
3. 电池的强化学习多种子重做。
4. 看板 v0.2：排序和敏感度页、资源视图。

**局限：**

- 两个重新计分的模块，真值都是 DFT，不是合成或实测。
- CSP 对照只有 11 个目标、一个模型（EquiCSP）、一个家族（钙钛矿框架），每组 3 次训练；ORB-v3 的模型版本是推断的。
- 离线的“实验次数”和“验证预算”都把每次验证当成一样贵；除了 CSP 对照的 GPU 花费，没有任何一笔投入的真实成本。
- 两次商业证据关卡各用了 28 次检索，只回答四个事先定好的问题。
- 市场层的很多数字来自系列文章，还没核实，看板里用灰色标出。
- 三种角色视角（科学验证、商业策略、S&O）用来组织问题，不代表任何人的意见。

**来源：** `modules/csp/RANDOM_REMOVAL_CONTROL.md`、`results/csp_r_eval_20261124T0335Z/report.md`、`modules/csp/REPORT.md`、`modules/battery/REPORT.md`、`modules/battery/COMMERCIAL_EVIDENCE_GATE.md`、`modules/thermal/REPORT.md`、`modules/thermal/COMMERCIAL_EVIDENCE_GATE.md`、`data/board/`（看板数据）。仓库：[github.com/dekunsun/materials-intelligence](https://github.com/dekunsun/materials-intelligence)。上一版：[Investment Decision Memo v2](memo_v2.md)。

---

## English version

Conclusion: CSP prototype dependence survives a pre-registered random-removal control. So larger-scale crystal screening stays deferred, and the next small sum goes to a test set further from known prototypes. Batteries keep two small internal investments and a limited-scope partnership; chip cooling stays on watch.

### Conclusion: three candidate investments

This memo replaces v2 (21 November 2026). Two pieces of evidence arrived after v2: the battery commercial evidence gate (21 November) and the CSP random-removal control (24 November). The basis is three technical modules, two commercial evidence gates and the 48 evidence rows on the board.

| Candidate investment | Decision | Why | Small step to take first |
| --- | --- | --- | --- |
| Larger-scale crystal screening | Defer | On substitution-generated candidates, 48 models already pick at least 95% DFT-stable structures at a 1% budget; more compute buys more candidates from the same distribution. The CSP control shows that the generative model depends on the perovskite frameworks in its training set for these targets. There is still no evidence further from known prototypes | Build a test set further from known prototypes and see whether models still separate and add value there. Write the design first, then decide whether to spend compute |
| More complete chip-cooling engineering tests | Watch | The problem is real and the acceptance metric is known (OCP cold-plate thermal resistance), but every buyer-side primary source points to cooling architecture; none says the material is the limit | On the internal-adoption path, a cheap next step is to ask one's own packaging team which layer dominates thermal resistance and whether a material could change it (inference) |
| A new solid-electrolyte experimental partnership | Approve (limited scope) | The battery gate found buyer-side cell-level metrics (Volkswagen: 700 cycles with at most 20% capacity loss, no test conditions stated; USABC cell targets). The material limit buyers name is interface durability, not conductivity; there is no buyer-side conductivity threshold | Joint exploration only, with milestones on cell-level metrics with stated test conditions (temperature, C-rate). The two small internal investments (curate existing measured data; run a small set of exploration samples before entering a new family) stay |

This is a practice memo built on public data only. Every recommendation is an inference and does not represent DeepMind's plans.

### 1. New evidence: the CSP random-removal control

With the perovskite frameworks removed, consensus is 3, 4 and 4; with the same number of structures removed at random, it is 8, 8 and 8. Under the rules written in advance, the outcome is template_specific.

**The question.** Wei et al. ([arXiv:2609.26502](https://arxiv.org/abs/2609.26502) v2) retrained EquiCSP without the perovskite frameworks, and its consensus recovery of 11 targets of type 1:1:2:6 fell from 8 to 3. The paper does not say whether the drop comes from losing those particular templates or simply from having less training data.

**Design (committed to git on 21 November 2026, before any training).**

- Both arms remove the ABC2D6 family. The PEROV arm also removes 1,268 perovskite-framework structures; the R arms remove the same number of other structures at random. The training sets are the same size (24,317), with the same recipe, seeds and scoring.
- Each arm has 3 training seeds (42, 43, 44), each trained from scratch for 106,000 steps on RunPod A5000s. Sampling, ORB-v3 relaxation and scoring ran on a Mac CPU.
- Decision rules: every R run beats every PEROV run and the mean difference is at least 3 → template_specific; mean difference at most 1 → data_amount; otherwise → inconclusive. The decision script was committed before any R result existed.

| Relaxed consensus (11 targets) | seed 42 | seed 43 | seed 44 | Mean |
| --- | --- | --- | --- | --- |
| PEROV: perovskite frameworks removed | 3 | 4 | 4 | 3.67 |
| R1–R3: the same number removed at random | 8 | 8 | 8 | 8.00 |

- The difference sits in 5 targets (mp-6231, mp-19093, mp-16307, mp-6603, mp-6389): the R arms recover them almost every time, and the PEROV arm never does, on any seed.
- The unrelaxed results give the same outcome. No arm's train or validation split contains a target, or a structure with a target's reduced formula.
- GPU cost was about $19 (7 full runs and 2 short 1,000-step test runs; price × time, not checked against billing).

**What it shows.** In this setup, PEROV's drop is not explained by less data. The model's recovery of these targets depends on the perovskite-framework structures in its training set.

**What it does not show.**

- Which framework structures matter, or how the model uses them.
- Whether this carries over to other families, other models or larger test sets.
- The sample is small: 3 runs per arm, and the exact permutation p is 1/20, the smallest 3 vs 3 can give; it does not decide anything. The ABC2D6 arm was trained once. The ORB-v3 model variant is inferred, not confirmed.

**What it means for decisions.** The claim "AI can discover new structures" has evidence near known prototypes and none away from them. So larger-scale crystal screening stays deferred, and the next small sum goes to a test set further from known prototypes. See `results/csp_r_eval_20261124T0335Z/report.md` and `modules/csp/RANDOM_REMOVAL_CONTROL.md`.

### 2. Scientific evidence and buyer demand

All three modules follow the same standard: the design is registered before running; baselines include a domain rule or older models, not only random; post-hoc analyses are labelled; an independent agent reviews the work and the fixes are applied. Both re-scoring modules match the official leaderboard value by value.

| Module | What was done | What it shows | What it does not show |
| --- | --- | --- | --- |
| Solid-state electrolytes | 499 measured OBELiX compositions as an offline lab, comparing six selection policies | In known families, prior measured data saves far more experiments than algorithm differences; with whole doping series held out, ML beats the "test sulfides first" rule by only 3–4 experiments | Whether transfer across families is reliable (sulfides yes, oxides no); whether RL has a stable advantage (one policy trained per split) |
| Chip cooling | Re-score of 62 models on κ_SRME; a rule baseline; measured values for 7 materials | On 103 simple binary compounds, the better models rank high-conductivity candidates almost identically; the rule misses BAs, the models do not | That real discovery is solved (the test set is too easy); that DFT matches measurement (6 of 7 materials 10–27% low); that known materials can be built into devices |
| Stability screening & CSP | Re-score of 73 models on WBM (215,488 candidates), read as a validation-budget decision; audit of one CSP benchmark paper; 7 from-scratch EquiCSP runs for the random-removal control the paper lacks | At small budgets most models pick well (1% budget: 48 models ≥ 95% stable, random 15.5%); past the confident candidates, top models are right about 90% of the time, CHGNet 39%; the generative model's recovery of 1:1:2:6 targets depends on the perovskite frameworks in its training set (Section 1) | That generative models produce structures further from known prototypes; whether optimising a generator against a potential is safe; whether DFT-stable structures can be synthesised |

**The shape across the three modules (hypothesis, not tested as a whole):** in the easy parts — interpolation within a doping series, simple binary compounds, small-budget screening — models already agree well with their computational reference, and the remaining uncertainty sits at the edges. The CSP control is the first point in this hypothesis to go through a pre-registered control: away from the prototypes in its training set, the generative model's recovery drops clearly. The edges in the other two modules have no such control yet.

| Direction | Demand-side evidence | Status |
| --- | --- | --- |
| Chip cooling | Commercial evidence gate (four pre-set questions, primary sources only, within 30 searches): who has the problem, how big it is and how buyers accept a solution all have primary evidence; "why a new material is needed" does not | Gate run; direction moved to watch |
| Solid-state electrolytes | Gate in the same format (rules committed to git before any search, commit `80f062e`): Q1–Q3 pass, Q3 with caveats (Volkswagen's 700-cycle target states no test conditions); Q4 passes, but the material limit the buyer names is interface durability (Toyota), and the buyer side also names manufacturing (Volkswagen); no buyer-side conductivity threshold | Gate run; partnership moved to approve (limited scope) |
| Stability screening & CSP | Not a market but a capability every direction depends on; demand comes from the directions it serves | Not applicable |
| Superconductors, fusion software, 2D materials | Only a few primary items at the market layer (for example, CFS ordering more than 10,000 km of tape from Fujikura); no technical module | Not evaluated |

Both gates point the same way: what holds buyers back is not the step this project backtests. Cooling buyers point to cooling architecture, not new materials; battery buyers point to interface durability and manufacturing, not conductivity. All sources are in `data/thermal/literature_sources.csv` and `data/battery/literature_sources.csv`.

### 3. Portfolio: near term, approve only cheap investments that can be checked quickly

Near-term commercial impact and long-term scientific value are listed separately and not merged into one score; without cost data, no ROI is given. These tables match the board's `data/board/decisions.csv`.

**Near-term commercial impact**

| Investment | Decision | Constraining resource | Continue if | Stop if |
| --- | --- | --- | --- | --- |
| Battery: curate existing measured conductivity data | Approve | Data | With the new data, a series-held-out backtest still beats the family rule and the intervals stop overlapping | Still indistinguishable from the family rule when series are held out |
| Battery: run a small set of exploration samples when entering a new family | Approve (limited scope) | Lab experiments | The model's ranking matches measurements in the first few experiments | Rankings disagree: fall back to the family rule or random exploration |
| Battery: RL-based material selection | Defer | Compute | After a multi-seed rerun, beats screening on official, cv5 and series-grouped splits | Fails to beat screening on any split |
| Battery: partnership talks with a battery maker (joint exploration only) | Approve (limited scope) | Partners | The partner agrees milestones on cell-level metrics with stated test conditions (temperature, C-rate) | No partner will commit to cell-level test conditions, or the talks require claims beyond the conductivity evidence |
| CSP: larger-scale crystal screening compute | Defer | Compute | A test set further from known prototypes shows models still separate and add value there | Models fail on that test set as badly as templates |
| Cooling: improve general models' κ scores to find thermal materials | Do not fund | Compute | On a harder dataset with complex structures, model rankings diverge | — |
| Cooling: discover new thermal materials | Watch | Compute and lab | A buyer (not a supplier) publicly names a material as the limit and will pay for it | — |
| Cooling: build known high-conductivity materials into devices (the fuller engineering tests) | Watch | Partners | Diamond-cooled servers get an independent test reported as OCP thermal resistance or junction temperature | — |

One further item is a hypothesis, not a decision: a synthesis and structure-confirmation partner for the top DFT-stable candidates. Its precondition is a literature backtest showing that a useful share of DFT-stable predictions do get synthesised.

**Long-term scientific value**

| Investment | Decision | Constraining resource | Continue if | Stop if |
| --- | --- | --- | --- | --- |
| CSP: add the random-removal control and repeated seeds | Done: prototype dependence held (24 November 2026) | Compute (small, about $19) | Met: prototype dependence survives the control, so the next step tests generative models further from known prototypes | Did not happen: the drop did not disappear under the size-matched random removal, and G0 reproduced the paper's consensus for both arms |
| Cooling: physics of the thermal reference calculation (four-phonon, defects) | Defer | Compute | Restart when chip cooling returns to priority | — |

### 4. What changed since v2

- **The CSP control is done, and the outcome is template_specific.** In the long-term table this item moves from approve (limited scope) to done; the deferral of larger-scale crystal screening rests on firmer grounds.
- **The battery gate's result is now in the main text.** v2 recorded it in an update box: the partnership moved from defer to approve (limited scope), with continue and stop conditions on cell-level metrics with stated test conditions.
- **The cooling decisions are unchanged.** Still on watch.
- **Board evidence grows from 40 to 48 rows.** The new rows are the battery gate's primary sources, the paper's paired ABC2D6-vs-PEROV comparison, and the CSP control's result (E048).
- **v2 is kept as a record.** Its two update boxes are folded into this memo.

### 5. What would change this recommendation

| If this happens | What changes |
| --- | --- |
| On a test set further from known prototypes, models still separate and add value | Larger-scale crystal screening moves from defer to candidate investment |
| On that test set, models fail as badly as templates | Crystal-screening compute is no longer a candidate; "AI discovers new structures" holds only near known prototypes |
| After two more ABC2D6 seeds, consensus without the template loss also varies a lot | The reading of the CSP control has to be revisited; so far all three random arms scored 8, so the variation looks small |
| A buyer (not a supplier) publicly names a thermal material as the limit and will pay for it; or the packaging team says thermal resistance sits mainly in a material layer | Cooling moves from watch to candidate investment, starting with device integration of known materials |
| After a multi-seed rerun, RL beats computational screening on every split | RL selection moves to a small pilot |
| No battery maker will commit to cell-level test conditions | The partnership stops; the two small internal investments stay |

**Next steps (by dependency, not by calendar):**

1. A stability test set further from known prototypes: write the design first, covering data sources, leakage into each model's training set and the decision rules; decide on any compute only after the design is agreed.
2. Optional: two more ABC2D6 seeds, 43 and 44 (about $5, paid, needs its own approval), to measure training variation without the template loss directly. They would not change this decision.
3. The multi-seed RL rerun for batteries.
4. Board v0.2: a ranking and sensitivity page, and a resource view.

**Limits:**

- In both re-scoring modules the truth is DFT, not synthesis or measurement.
- The CSP control covers only 11 targets, one model (EquiCSP) and one family (perovskite frameworks), with 3 runs per arm; the ORB-v3 model variant is inferred.
- Offline "experiment counts" and "validation budgets" treat every validation as equally expensive; apart from the CSP control's GPU cost, there is no real cost data for any investment.
- Each commercial evidence gate used 28 searches and answers only four pre-set questions.
- Many market-layer numbers come from the series article and are unverified; the board shows them in grey.
- The three role lenses (scientific validation, commercial strategy, S&O) organise the questions; they do not represent anyone's views.

**Sources:** `modules/csp/RANDOM_REMOVAL_CONTROL.md`, `results/csp_r_eval_20261124T0335Z/report.md`, `modules/csp/REPORT.md`, `modules/battery/REPORT.md`, `modules/battery/COMMERCIAL_EVIDENCE_GATE.md`, `modules/thermal/REPORT.md`, `modules/thermal/COMMERCIAL_EVIDENCE_GATE.md`, `data/board/` (board data). Repository: [github.com/dekunsun/materials-intelligence](https://github.com/dekunsun/materials-intelligence). Previous version: [Investment Decision Memo v2](memo_v2.md).
