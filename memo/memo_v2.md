<!-- Exported from Claude Docs on 2026-11-24. -->

# Investment Decision Memo v2：三个模块、三笔候选投入

2026-11-21 · Dekun Sun

三笔候选投入都不建议现在大额批准。每一笔前面，都有一个更便宜、能改变决定的信息步骤，应该先做；这些小步骤建议批准。

## 结论：三笔候选投入

这份备忘录回答评审提出的检验场景：现在有三笔候选投入，哪一笔该批准，哪一笔该暂缓？依据是三个技术模块、一次商业证据关卡和看板里的 40 条证据。

| 候选投入 | 决定 | 为什么 | 先做的小步骤 |
| --- | --- | --- | --- |
| 更大规模的晶体筛选 | 暂缓 | 在元素替换生成的候选上，1% 预算已有 48 个模型挑到至少 95% DFT 稳定的结构；多花算力买到的是更多同一分布的候选。离已知原型更远的地方还没有证据；CSP 基准上生成模型没有超过模板 | 批准小额算力：补 CSP 论文缺的随机移除对照和多种子重训；再建一个离已知原型更远的测试集 |
| 更完善的芯片散热工程测试 | 观察 | 问题是真的，验收指标也已知（OCP 冷板热阻）；但买家一侧的一手来源都指向冷却架构，没有一家说材料是限制 | 如果走"内部采用"路径，最便宜的下一步是问自己的封装团队：热阻里哪一层最大、材料能不能改变它（推断） |
| 新的固态电解质实验合作 | 批准（限定范围） | 回测里的 10⁻³ S/cm 是研究筛选阈值，不是电池厂标准；电化学窗口、界面等后几道关卡没有买家数字；迁移到新化学家族是否有效，事先看不出 | 批准两笔内部小投入：整理已有实测数据；进入新家族时先做一小组探索性样本。谈合作之前，先过一次同格式的商业证据关卡 |

**一句话：** 三个模块都显示，在容易的部分，模型已经和计算参考对得很好；不确定的都在边缘——新化学家族、离已知原型更远的结构、计算参考和实验之间、买家到底要不要新材料。钱先花在把这些边缘问清楚的小步骤上，而不是大项目上。

> **更新（2026-11-21，电池商业证据关卡之后）：** 关卡规则在检索前提交到 git（commit `80f062e`）。结果：Q1–Q3 过；Q4 过，但买家点名的材料限制是界面耐久性（丰田），不是电导率，买家一侧也点名了制造（大众）。买家侧验收指标找到了：大众的 700 次循环、容量损失不超过 20%（没有测试条件），以及 USABC 的电芯目标。按事先定好的规则，**“新的固态电解质实验合作”从暂缓改为批准（限定范围）**：只谈联合探索，里程碑按带测试条件的电芯级指标设。上表和第 3 节的决定已更新；理由和条件两栏保留 v2 原文。电导率没有买家侧门槛，10⁻³ S/cm 仍是研究筛选阈值。详见 `modules/battery/COMMERCIAL_EVIDENCE_GATE.md`。

> **更新（2026-11-24，CSP 随机移除对照之后）：** 对照的规则在任何训练之前提交到 git（commit `4220c46`、`36067ae`），判定脚本在任何随机组结果出来之前 commit（`57970a3`）。结果：在 11 个 1:1:2:6 目标上，去掉 1,268 个钙钛矿框架结构时弛豫后 consensus 是 3、4、4，随机去掉同样数量时是 8、8、8。按事先定好的规则，结论是“模板特有”：**原型依赖在对照后仍成立**。所以第 3 节长期科学价值表里，“补做随机移除对照和多种子重训”改为**已完成**，继续条件已满足，下一步是离已知原型更远的测试集；“更大规模的晶体筛选”仍暂缓，理由更充分。范围：只有 11 个目标、一个模型（EquiCSP），每组 3 次训练（ABC2D6 组 1 次），没有说明是哪些结构起作用。GPU 花费约 $19（估算）。详见 `results/csp_r_eval_20261124T0335Z/report.md`。

这是一份练习备忘录，只用公开数据，所有建议都是推断，不代表 DeepMind 的计划。

## 1. 科学证据：三个模块，同一套标准

三个模块都按同一套标准做：设计在运行前登记；基线包括领域经验规则或老一代模型，不只是随机；事后分析单独标明；跑完后请独立代理审查并改正。两个重新计分的模块都和官方排行榜逐个对上。

| 模块 | 做了什么 | 证明了什么 | 没有证明什么 |
| --- | --- | --- | --- |
| 固态电解质 | OBELiX 499 个实测组成当离线实验室，比较六种选材策略 | 已知家族里，先验实测数据省下的实验远多于算法差别；但把同一掺杂系列整个留出后，机器学习只比"先测硫化物"的规则多省 3–4 次 | 跨家族迁移是否可靠（硫化物有效、氧化物无效）；强化学习是否有稳定优势；电池厂的真实门槛 |
| 芯片散热 | 62 个模型的 κ_SRME 重新计分；经验规则基线；7 个材料的实测对照 | 在 103 个简单二元化合物上，较好的模型对高导热候选的排序几乎一致；规则漏掉 BAs，模型没有 | 真实发现问题已解决（测试集太容易）；DFT 接近实测（7 个里 6 个低 10–27%）；已知材料能装进器件 |
| 稳定性筛选与 CSP | 73 个模型在 WBM（215,488 个候选）上重新计分，按"给定验证预算"来读；审计一篇 CSP 基准论文 | 小预算下大多数模型都挑得准（1% 预算：48 个模型 ≥ 95% 稳定，随机 15.5%）；超出"有把握"的候选后，前列模型约 90% 对，CHGNet 39% | 生成模型能产生真正新的结构；对生成器做势函数优化是否安全；DFT 稳定的结构能不能合成 |

**三个模块合起来的形状（假设，未检验）：** 在容易的部分——同一掺杂系列内插值、简单二元化合物、小预算筛选——模型已经和计算参考对得很好。剩下的不确定都在边缘。对资源分配来说，这意味着提高通用模型分数的边际价值在下降，而把边缘问清楚的信息价值在上升。

## 2. 买家需求：只有散热过了关卡

| 方向 | 需求侧证据 | 状态 |
| --- | --- | --- |
| 芯片散热 | 商业证据关卡（事先定好四个问题、只认一手来源、30 次检索内）：谁有问题、问题多大、怎么验收都有一手依据；"为什么需要新材料"没有 | 已过关；方向降为观察 |
| 固态电解质 | 电芯级采购门槛等数字来自系列文章，未核实；回测用的 10⁻³ S/cm 是研究筛选阈值 | 尚未过关 |
| 稳定性筛选与 CSP | 不是一个市场，而是所有方向都依赖的能力；需求要看它服务的方向 | 不适用 |
| 超导、聚变软件、二维材料 | 只有市场层的少数一手证据（例如 CFS 向 Fujikura 订购超过 1 万公里带材），没有技术模块 | 未评估 |

散热关卡的结果改变了 v1 之前的工作假设：买家（微软、Google Cloud、TSMC）都把方向放在冷却架构上：TSMC 说导热界面材料限制散热，但方向是去掉这一层。唯一的付钱证据（Akash 与 NxtGen 的 2700 万美元合同）是供应商自己说的，没有独立测试。所有来源在 `data/thermal/literature_sources.csv`。

## 3. 投资组合：近期只批准便宜、能快速检验的投入

近期商业影响和长期科学价值分开列，不合成一个总分；没有成本数据，不写投资回报率。这张表和看板的 `data/board/decisions.csv` 一致。

**近期商业影响**

| 投入 | 决定 | 卡住的资源 | 继续条件 | 停止条件 |
| --- | --- | --- | --- | --- |
| 电池：整理已有实测电导率数据 | 批准 | 数据 | 加入新数据后，按系列留出的回测仍优于家族规则，且区间不再重叠 | 按系列留出时仍和家族规则分不出来 |
| 电池：进入新家族时先做一小组探索性样本 | 批准（限定范围） | 实验 | 前几次实验里模型排序和实测一致 | 排序不一致：退回家族规则或随机探索 |
| 电池：用强化学习选材 | 暂缓 | 算力 | 多种子重做后，在所有划分上都优于计算筛选 | 任一划分上不优于计算筛选 |
| 电池：和电池厂谈合作 | 批准（限定范围） | 伙伴 | 同格式的商业证据关卡拿到买家侧验收指标 | 关卡里找不到买家侧验收指标 |
| CSP：更大规模的晶体筛选算力 | 暂缓 | 算力 | 离已知原型更远的测试集上，模型仍有区分和增量价值 | 模型在那里和模板一样失败 |
| 散热：为找导热材料提升通用模型的 κ 分数 | 不投入 | 算力 | 更难、含复杂结构的数据集上，模型排序分歧变大 | — |
| 散热：发现新的导热材料 | 观察 | 算力和实验 | 一个买家（不是供应商）公开说某种材料是限制并愿意付钱 | — |
| 散热：已知高导热材料的器件化（即更完善的工程测试） | 观察 | 伙伴 | 金刚石散热服务器有按 OCP 热阻或结温报告的独立测试 | — |

另有一项假设，不是决定：为 DFT 稳定的头部候选找合成与结构确认伙伴。前提是一次文献回测显示，DFT 稳定的预测有可观比例被合成出来。

**长期科学价值**

| 投入 | 决定 | 卡住的资源 | 继续条件 | 停止条件 |
| --- | --- | --- | --- | --- |
| CSP：补做随机移除对照和多种子重训 | 已完成：原型依赖成立（2026-11-24） | 算力（小） | 对照后原型依赖仍成立：再在离已知原型更远处测试生成模型 | 同等规模随机移除下，下降消失 |
| 散热：热导率参考计算的物理（四声子、缺陷） | 暂缓 | 算力 | 散热回到优先时再启动 | — |

## 4. 与 v1 相比改了什么

- **新增稳定性筛选与 CSP 模块。** 由此增加两项决定：更大规模的晶体筛选暂缓；补 CSP 论文缺的对照（小额算力）批准。
- **直接回答评审的检验场景。** v1 按方向组织，v2 先回答"三笔候选投入各怎么处理"。
- **电池和散热的决定没有变。** 散热仍是观察；电池仍是两笔小投入批准、强化学习和合作暂缓。
- **有了可以查的依据。** 每条证据和每项决定都在投资组合看板 v0.1 里，带出处和核实状态；代码和运行记录已进 git（commit `677176a`）。
- **跨模块的"形状"写成假设，** 不作为结论。

## 5. 什么信息会改变这份建议

| 如果出现 | 会改变什么 |
| --- | --- |
| 一个买家（不是供应商）公开说某种散热材料是限制并愿意付钱；或内部封装团队说热阻主要在材料层 | 散热从观察回到候选投入，先做已知材料的器件化 |
| 离已知原型更远的测试集上，模型仍有区分和增量价值 | 更大规模的晶体筛选从暂缓改为候选投入 |
| 对照后 CSP 的原型依赖消失 | 生成式 CSP 的证据变强，可以考虑追加算力（2026-11-24：没有出现，对照后原型依赖仍成立） |
| 多种子重做后，强化学习在所有划分上稳定优于计算筛选 | 强化学习选材改为小规模试点 |
| 电池的商业证据关卡拿到买家侧验收指标 | 可以和电池厂谈联合探索，里程碑按这些指标设 |

**下一步（按依赖关系，不按日历）：** （电池的商业证据关卡和 CSP 对照实验已完成）离已知原型更远的稳定性测试集 → 强化学习多种子重做 → 看板 v0.2（排序和敏感度页、资源视图）。

**局限：**

- 三个模块用的都是已发表的数据；两个重新计分的模块，真值都是 DFT，不是合成或实测。
- 离线的"实验次数"和"验证预算"都把每次验证当成一样贵；没有任何一笔投入的真实成本。
- 商业证据关卡只用了 28 次检索，只回答四个事先定好的问题。
- 市场层的很多数字来自系列文章，还没核实，看板里用灰色标出。
- 三种角色视角（科学验证、商业策略、S&O）用来组织问题，不代表任何人的意见。

**来源：** `modules/battery/REPORT.md`、`modules/thermal/REPORT.md`、`modules/thermal/COMMERCIAL_EVIDENCE_GATE.md`、`modules/csp/REPORT.md`、`data/board/`（看板数据）、`data/thermal/literature_sources.csv`。看板运行方式：`.venv/bin/streamlit run board/app.py`。上一版：[Investment Decision Memo 01](memo_01.md)。

---

## English version

None of the three candidate investments should be approved at scale now. Each one has a cheaper information step in front of it that could change the decision; those small steps are recommended for approval.

### Conclusion: three candidate investments

This memo answers the review's test scenario: of three candidate investments, which should be approved and which deferred? The evidence is three technical modules, one commercial evidence gate and the 40 evidence rows on the board.

| Candidate investment | Decision | Why | Small step to take first |
| --- | --- | --- | --- |
| Larger-scale crystal screening | Defer | On substitution-generated candidates, 48 models already pick at least 95% DFT-stable structures at a 1% budget; more compute buys more candidates from the same distribution. There is no evidence yet further from known prototypes, and on the CSP benchmark generative models do not beat templates | Approve a little compute for the random-removal control and repeated seeds the CSP paper lacks, then build a test set further from known prototypes |
| More complete chip-cooling engineering tests | Watch | The problem is real and the acceptance metric is known (OCP cold-plate thermal resistance), but every buyer-side primary source points to cooling architecture; none says the material is the limit | On the internal-adoption path, the cheapest next step is to ask one's own packaging team which layer dominates thermal resistance and whether a material could change it (inference) |
| A new solid-electrolyte experimental partnership | Approve (limited scope) | The backtest's 10⁻³ S/cm is a research screening threshold, not a battery-maker standard; later gates such as electrochemical window and interfaces have no buyer numbers; whether transfer to a new chemical family works cannot be predicted | Approve two small internal investments: curate existing measured data, and run a small set of exploration samples before entering a new family. Before partnership talks, pass a commercial evidence gate in the same format |

**In one sentence:** all three modules show that in the easy parts, models already agree well with their computational reference; the uncertainty sits at the edges — new chemical families, structures further from known prototypes, the gap between computational reference and experiment, and whether buyers want a new material at all. Money should first go to small steps that settle those edges, not to large projects.

> **Update (21 November 2026, after the battery commercial evidence gate):** the gate's rules were committed to git before any search (commit `80f062e`). Result: Q1–Q3 pass; Q4 passes, but the material limit the buyer names is interface durability (Toyota), not conductivity, and the buyer side also names manufacturing (Volkswagen). Buyer-side acceptance metrics were found: Volkswagen's 700 cycles with at most 20% capacity loss (no test conditions), and USABC's cell targets. Under the pre-set rules, **"a new solid-electrolyte experimental partnership" moves from defer to approve (limited scope)**: joint exploration only, with milestones on cell-level metrics with stated test conditions. The decision in the table above and in Section 3 is updated; the rationale and condition columns keep the original v2 text. No buyer-side conductivity threshold exists; 10⁻³ S/cm remains a research screening threshold. See `modules/battery/COMMERCIAL_EVIDENCE_GATE.md`.

> **Update (24 November 2026, after the CSP random-removal control):** the control's rules were committed to git before any training (commits `4220c46`, `36067ae`), and the decision script before any random-arm result existed (`57970a3`). Result: on the 11 targets of type 1:1:2:6, relaxed consensus is 3, 4 and 4 with the 1,268 perovskite-framework structures removed, and 8, 8 and 8 with the same number removed at random. Under the pre-set rules the outcome is template_specific: **prototype dependence survives the control**. So in Section 3's long-term table, "add the random-removal control and repeated seeds" is now **done**; its continue condition is met, and the next step is a test set further from known prototypes. "Larger-scale crystal screening" stays deferred, on firmer grounds. Scope: only 11 targets, one model (EquiCSP), 3 runs per arm (1 for ABC2D6), and nothing about which structures matter. GPU cost was about $19 (estimate). See `results/csp_r_eval_20261124T0335Z/report.md`.

This is a practice memo built on public data only. Every recommendation is an inference and does not represent DeepMind's plans.

### 1. Scientific evidence: three modules, one standard

All three modules follow the same standard: the design is registered before running; baselines include a domain rule or older models, not only random; post-hoc analyses are labelled; an independent agent reviews the work and the fixes are applied. Both re-scoring modules match the official leaderboard value by value.

| Module | What was done | What it shows | What it does not show |
| --- | --- | --- | --- |
| Solid-state electrolytes | 499 measured OBELiX compositions as an offline lab, comparing six selection policies | In known families, prior measured data saves far more experiments than algorithm differences; with whole doping series held out, ML beats the "test sulfides first" rule by only 3–4 experiments | Whether transfer across families is reliable (sulfides yes, oxides no); whether RL has a stable advantage; the real battery-maker gates |
| Chip cooling | Re-score of 62 models on κ_SRME; a rule baseline; measured values for 7 materials | On 103 simple binary compounds, the better models rank high-conductivity candidates almost identically; the rule misses BAs, the models do not | That real discovery is solved (the test set is too easy); that DFT matches measurement (6 of 7 materials 10–27% low); that known materials can be built into devices |
| Stability screening & CSP | Re-score of 73 models on WBM (215,488 candidates), read as a validation-budget decision; audit of one CSP benchmark paper | At small budgets most models pick well (1% budget: 48 models ≥ 95% stable, random 15.5%); past the confident candidates, top models are right about 90% of the time, CHGNet 39% | That generative models produce genuinely new structures; whether optimising a generator against a potential is safe; whether DFT-stable structures can be synthesised |

**The shape across the three modules (hypothesis, untested):** in the easy parts — interpolation within a doping series, simple binary compounds, small-budget screening — models already agree well with their computational reference. The remaining uncertainty sits at the edges. For resource allocation, this means the marginal value of raising general model scores is falling, while the value of information from settling the edges is rising.

### 2. Buyer demand: only chip cooling has passed a gate

| Direction | Demand-side evidence | Status |
| --- | --- | --- |
| Chip cooling | Commercial evidence gate (four pre-set questions, primary sources only, within 30 searches): who has the problem, how big it is and how buyers accept a solution all have primary evidence; "why a new material is needed" does not | Gate passed; direction moved to watch |
| Solid-state electrolytes | Numbers such as the cell-level purchase threshold come from the series article and are unverified; the backtest's 10⁻³ S/cm is a research screening threshold | Gate not yet run |
| Stability screening & CSP | Not a market but a capability every direction depends on; demand comes from the directions it serves | Not applicable |
| Superconductors, fusion software, 2D materials | Only a few primary items at the market layer (for example, CFS ordering more than 10,000 km of tape from Fujikura); no technical module | Not evaluated |

The cooling gate changed the working hypothesis held before v1: buyers (Microsoft, Google Cloud, TSMC) all put the emphasis on cooling architecture; TSMC says thermal interface materials limit cooling, but its direction is to remove that layer. The only evidence of payment (Akash's $27 million contract with NxtGen) comes from the supplier itself, with no independent test. All sources are in `data/thermal/literature_sources.csv`.

### 3. Portfolio: near term, approve only cheap investments that can be checked quickly

Near-term commercial impact and long-term scientific value are listed separately and not merged into one score; without cost data, no ROI is given. This table matches the board's `data/board/decisions.csv`.

**Near-term commercial impact**

| Investment | Decision | Constraining resource | Continue if | Stop if |
| --- | --- | --- | --- | --- |
| Battery: curate existing measured conductivity data | Approve | Data | With the new data, a series-held-out backtest still beats the family rule and the intervals stop overlapping | Still indistinguishable from the family rule when series are held out |
| Battery: run a small set of exploration samples when entering a new family | Approve (limited scope) | Lab experiments | The model's ranking matches measurements in the first few experiments | Rankings disagree: fall back to the family rule or random exploration |
| Battery: RL-based material selection | Defer | Compute | After a multi-seed rerun, beats computational screening on every split | Fails to beat screening on any split |
| Battery: partnership talks with a battery maker | Approve (limited scope) | Partners | A commercial evidence gate in the same format obtains buyer-side acceptance metrics | The gate finds no buyer-side acceptance metric |
| CSP: larger-scale crystal screening compute | Defer | Compute | On a test set further from known prototypes, models still separate and add value | Models fail there as badly as templates |
| Cooling: improve general models' κ scores to find thermal materials | Do not fund | Compute | On a harder dataset with complex structures, model rankings diverge | — |
| Cooling: discover new thermal materials | Watch | Compute and lab | A buyer (not a supplier) publicly names a material as the limit and will pay for it | — |
| Cooling: build known high-conductivity materials into devices (the fuller engineering tests) | Watch | Partners | Diamond-cooled servers get an independent test reported as OCP thermal resistance or junction temperature | — |

One further item is a hypothesis, not a decision: a synthesis and structure-confirmation partner for the top DFT-stable candidates. Its precondition is a literature backtest showing that a useful share of DFT-stable predictions do get synthesised.

**Long-term scientific value**

| Investment | Decision | Constraining resource | Continue if | Stop if |
| --- | --- | --- | --- | --- |
| CSP: add the random-removal control and repeated seeds | Done: prototype dependence held (24 November 2026) | Compute (small) | Prototype dependence survives the controls: then test generative models further from known prototypes | The drop disappears under a size-matched random removal |
| Cooling: physics of the thermal reference calculation (four-phonon, defects) | Defer | Compute | Restart when chip cooling returns to priority | — |

### 4. What changed since v1

- **Added the stability screening & CSP module.** Two new decisions follow: defer larger-scale crystal screening; approve the missing CSP controls (a little compute).
- **The review's test scenario is answered directly.** v1 was organised by direction; v2 first answers "what to do with each of the three candidate investments".
- **Battery and cooling decisions are unchanged.** Cooling remains on watch; in batteries, two small investments are approved and RL and partnership talks are deferred.
- **The evidence can now be checked.** Every evidence row and every decision is on Portfolio Board v0.1 with its source and verification status; code and run records are in git (commit `677176a`).
- **The cross-module "shape" is stated as a hypothesis,** not a conclusion.

### 5. What would change this recommendation

| If this happens | What changes |
| --- | --- |
| A buyer (not a supplier) publicly names a thermal material as the limit and will pay for it; or the internal packaging team says thermal resistance sits mainly in a material layer | Cooling moves from watch to candidate investment, starting with device integration of known materials |
| On a test set further from known prototypes, models still separate and add value | Larger-scale crystal screening moves from defer to candidate investment |
| CSP prototype dependence disappears under the controls | The evidence for generative CSP strengthens; more compute can be considered (24 November 2026: did not happen; prototype dependence survived the control) |
| After a multi-seed rerun, RL beats computational screening on every split | RL selection moves to a small pilot |
| The battery commercial evidence gate obtains buyer-side acceptance metrics | Joint exploration with a battery maker becomes possible, with milestones set on those metrics |

**Next steps (by dependency, not by calendar):** (the battery commercial evidence gate and the CSP control experiments are done) a stability test set further from known prototypes → multi-seed RL rerun → board v0.2 (ranking and sensitivity page, resource view).

**Limits:**

- All three modules use published data; in both re-scoring modules the truth is DFT, not synthesis or measurement.
- Offline "experiment counts" and "validation budgets" treat every validation as equally expensive; there is no real cost data for any investment.
- The commercial evidence gate used 28 searches and answers only four pre-set questions.
- Many market-layer numbers come from the series article and are unverified; the board shows them in grey.
- The three role lenses (scientific validation, commercial strategy, S&O) organise the questions; they do not represent anyone's views.

**Sources:** `modules/battery/REPORT.md`, `modules/thermal/REPORT.md`, `modules/thermal/COMMERCIAL_EVIDENCE_GATE.md`, `modules/csp/REPORT.md`, `data/board/` (board data), `data/thermal/literature_sources.csv`. Run the board with `.venv/bin/streamlit run board/app.py`. Previous version: [Investment Decision Memo 01](memo_01.md).
