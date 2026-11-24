<!-- Exported from Claude Docs on 2026-11-24. -->

# Investment Decision Memo 01：固态电解质与芯片散热

2026-11-21 · Dekun Sun

建议批准电池上的两笔小投入（整理已有实测数据、进入新化学家族时的探索性样本），暂缓强化学习选材和电池厂合作，把芯片散热降为观察。散热的问题是真的，但买家一侧的一手来源都指向冷却架构，而不是新材料。

## 决策请求与结论

**请求：** 用两个回测和一次商业证据关卡，决定下一份资源投向固态电解质和芯片散热里的哪几笔投入。两个方向用同一套证据标准：科学上可信到哪一步、买家要不要、卡住的是哪类资源。

**三条结论：**

1. **电池：AI 的收益必须和化学家族规则比，而且同一掺杂系列内的插值会放大表面收益。** 钱先投数据，不投更复杂的选材算法。
2. **芯片散热：在 103 个简单二元化合物上，较好的模型对高导热候选的排序高度一致，但这不证明真实的材料发现问题已经解决。** DFT 参考值和实验测量之间、材料和器件之间都还有差距。商业证据关卡回答了谁有这个问题、问题有多大、用什么验收；但"为什么需要新材料"没有一手依据。
3. **组合：近期只批准成本低、能马上检验的投入，其余每笔都配一个可检查的继续条件。** 下一步进入稳定性筛选与 CSP 模块；电池的商业证据关卡放在任何电池厂对话之前。

这是一份练习备忘录，只用公开数据，所有建议都是推断。

## 1. 科学证据：两个回测各证明到哪一步

两个模块用同一套证据标准：设计在运行前登记；基线包括领域经验规则，不只是随机；事后分析单独标明；跑完后请独立代理审查并改正。

| 方向 | 做了什么 | 证明了什么 | 没有证明什么 |
| --- | --- | --- | --- |
| 固态电解质 | 把 OBELiX 的 499 个实测组成当离线实验室，比较六种选材策略找到电导率过线（研究筛选阈值 10⁻³ S/cm）材料所需的实验次数 | 在已知化学家族里，先验实测数据省下的实验次数，远多于选材算法之间的差别；一条"先测硫化物"的经验规则就拿到了大部分收益 | 跨家族迁移是否可靠（硫化物有效、氧化物无效，事先看不出）；强化学习是否有稳定优势（只训练了一个策略）；电池厂真实门槛 |
| 芯片散热 | 用自己重写的代码重新计分 Matbench Discovery κ_SRME 上全部 62 个模型，与排行榜完全一致；再用筛选指标、经验规则和 7 个材料的实测值去对照 | 在这 103 个简单二元化合物上，较好的模型对高导热候选的排序高度一致；经验规则漏掉了 BAs，模型没有 | 真实的材料发现问题已经解决（测试集前 10 名和第 11 名差 25%，太容易分开）；DFT 参考值接近实测（6 / 7 个材料低 10–27%）；已知材料能装进器件 |

**电池：AI 的收益必须和化学家族规则比，而且同一掺杂系列内的插值会放大表面收益。**

- 找到 5 个过线材料，随机约要 30 次实验（约四分之一的活动 40 次内没找到）。用先验数据训练的计算筛选，在随机分折时只要 5 次。
- 把同一掺杂系列整个留出后，计算筛选要 7.6–12.9 次；相对化学家族规则只多省 3–4 次，区间重叠或几乎重叠（事后分析）。
- 回测里的"实验次数"是读出一个已发表的数，不是实验成本；先验数据也被当成免费的。

**芯片散热：模型排序一致，不等于发现问题已解决。**

- 排行榜较好的一半（31 个模型）里，28 个给出完全相同的前 10 名。前 5 名模型离 DFT 参考值的中位差 2.9%。
- "四面体结构、轻原子"这条规则找到前 10 名里的 6 个，但把 BAs 排在第 21 名；SRME 低于 0.2 的模型都把 BAs 排进前 5。计算的价值在规则失效的地方。
- 两个差距还在：DFT 参考值和实验测量之间；以及材料到器件之间（GaN–金刚石界面热阻常见 20–30 m²K/GW，BAs 晶体仍是毫米级，商用 AlN 216–278 W/m·K 对本征 321）。

## 2. 买家需求：散热问题是真的，但买家要的是冷却架构，不是新材料

散热方向过了一次事先定好退出条件的商业证据关卡：只问四个问题，只认一手来源，最多 30 次检索（实用 28 次）。规则和结果在 `modules/thermal/COMMERCIAL_EVIDENCE_GATE.md`。

| 问题 | 结论 | 一手依据 |
| --- | --- | --- |
| 谁有这个问题？ | 过 | 微软、TSMC、Google Cloud 都在自己的材料里把加速器散热列为要解决的问题 |
| 问题有多大？ | 过 | AMD MI355X 板卡功耗 1400 W；NVIDIA DGX B200 每颗 GPU 最大 1000 W；H100 SXM 是 700 W |
| 用什么指标验收？ | 过 | OCP 冷板测试规范：壳到冷却液入口的热阻，在带导热界面材料的测试芯片上、约 45 °C 冷却液、多个流量下测；TSMC 另用给定功率下的结温和可靠性测试后的漏率 |
| 为什么需要新材料？ | 不过 | 买家一侧都指向冷却架构：微软微流体、Google 液冷、TSMC 去掉导热界面层的直接液冷。TSMC 说界面材料限制散热，但比较的是已知材料，方向是去掉这一层 |

- **唯一的"付钱"证据是供应商说的。** Akash 自己的新闻稿说和一家云厂商签了 2700 万美元的金刚石散热服务器合同；金刚石的类型和位置没公开，也没有独立测试。
- **没找到一手来源的，备忘录里不引用：** TSMC "封装功率 600 W 到 4100 W"的说法、GB300 的功耗、Akash 3 亿美元订单的买家。
- **固态电解质的买家需求还没过同样的关卡。** 10⁻³ S/cm 是研究筛选阈值，不是电池厂标准；电化学窗口、界面等后几道门槛的买家一侧数字也还没有。

## 3. 资源分配：只批准电池上的两笔小投入，其余暂缓或观察

近期批准的两笔都在电池：整理已有实测数据，以及进入新化学家族时的探索性样本。散热方向按商业证据关卡的规则降为观察。近期商业影响和长期科学价值分开排，不合成一个总分；没有成本数据，不写投资回报率。

| 投入 | 决定 | 理由 | 卡住的资源 | 继续条件 | 停止条件 |
| --- | --- | --- | --- | --- | --- |
| 电池：整理已有的实测电导率数据，用于已知家族的计算筛选 | 批准 | 已知家族里，先验数据省下的实验远多于算法之间的差别 | 数据 | 加入新数据后，按系列留出的回测里相对化学家族规则仍省实验，且区间不再重叠 | 加入新数据后，按系列留出仍和化学家族规则分不出来 |
| 电池：进入新化学家族时，先安排一小组探索性样本 | 批准（限定范围） | 迁移是否有效事先看不出：硫化物有效，氧化物无效 | 实验 | 前几次实验里，模型排序和实测一致，再放大预算 | 排序不一致就退回化学家族规则或随机探索 |
| 电池：用强化学习选材 | 暂缓 | 只训练了一个策略，没有稳定优势 | 算力 | 多种子重做后，在官方划分、cv5 和按系列分组上都稳定优于计算筛选 | 任一划分上不优于计算筛选 |
| 电池：和电池厂谈合作 | 暂缓 | 门槛是研究阈值；电化学窗口、界面等后几道关卡没有买家数字 | 伙伴 | 先过一次同格式的商业证据关卡，拿到买家一侧的验收指标 | 关卡里找不到买家一侧的验收指标 |
| 散热：为找导热材料提高通用模型的 κ 分数 | 不投入 | 较好的模型排序已一致，而且这个测试集太容易，证明不了什么 | 算力 | 在一个更难、含复杂结构的数据集上，模型之间的排序分歧变大 | — |
| 散热：发现新的导热材料 | 观察 | 没有一手证据表明买家需要新材料；买家一侧指向冷却架构 | 计算和实验 | 一个买家（不是供应商）公开说某种材料是限制，并愿意为它付钱 | — |
| 散热：已知高导热材料的器件化 | 观察 | 同上；唯一的付钱证据来自供应商，没有独立测试 | 伙伴 | 金刚石散热服务器有独立测试结果，按 OCP 热阻或结温报告 | — |
| 长期科学：热导率参考计算的物理（四声子、缺陷、和实测系统对比） | 暂缓 | 7 个材料里 6 个 DFT 比实测低 10–27%；能提高计算可信度，但不改变近期投资决定 | 算力 | 散热方向回到优先投入时再启动 | — |

不用"过了第几关"跨方向比较：散热的问题比电池更确定、验收指标也更清楚，但"需要新材料"这一条没有过。

## 4. 芯片散热的两条回报路径：材料发现 vs 器件验证

器件验证离回报更近：它用的是已经测到高导热的材料，卡在可以直接测量的界面和尺寸上。材料发现离回报更远：发现之后，还要走完器件验证那条路。没有可靠的成本数据，所以不算投资回报率，只比两条路上还有哪些关卡、下一份信息从哪里来。

|  | 材料发现 | 器件验证（已知高导热材料） |
| --- | --- | --- |
| 价值在什么时候到来 | 新材料比已知材料在器件里更好，并走完制备、界面、可靠性和买家验收 | 已知材料在买家的封装里，按买家的验收指标降低热阻或结温 |
| 中间还有哪些关卡 | 计算候选 → 参考计算可信 → 合成和测量 → 长成可用尺寸 → 界面和器件 → 买家验收 | 界面和器件 → 买家验收 |
| 现在的证据 | 在简单二元化合物上，模型排序已一致；对复杂结构没有证据。BAs 从计算预测（2013）到实测（2018）用了约 5 年，晶体至今仍是毫米级 | 界面热阻、晶圆尺寸、热膨胀匹配都有可测的数字；已有 GaN-on-金刚石射频器件在卖 |
| 最大的未知 | 复杂结构里有没有比已知材料更容易制造、界面更好的材料 | 买家是否需要材料方案，还是用冷却架构（微流体、直接液冷）解决；买家的验收指标是什么 |
| 下一份信息最便宜的来源 | 一个含复杂结构、前几名挨得更近的热导率数据集上的重新计分（纯计算） | 商业证据关卡（第 2 节，已完成），然后和买家或伙伴直接对话拿验收指标 |

两条路共用同一个前提：买家需要更好的散热材料。商业证据关卡没有找到这个前提的一手依据：买家一侧把方向放在冷却架构上。所以两条路现在都不作为优先投入；器件验证仍是离回报更近的那条，前提一旦成立应先做它。

## 5. 什么信息会改变这份建议

| 如果出现 | 会改变什么 |
| --- | --- |
| 一个买家（不是供应商）公开说某种散热材料是限制，并愿意为它付钱 | 散热从观察回到候选投入，先做已知材料的器件化 |
| 金刚石散热服务器有按 OCP 热阻或结温报告的独立测试 | 同上 |
| 在更难、含复杂结构的热导率数据集上，模型排序分歧变大 | 提高模型精度重新成为有意义的计算投入 |
| 多种子重做后，强化学习在所有划分上都稳定优于计算筛选 | 强化学习选材从暂缓改为小规模试点 |
| 电池的商业证据关卡拿到买家一侧的验收指标 | 可以和电池厂谈联合探索，里程碑按这些指标设 |

**下一步（按依赖关系）：** 稳定性筛选与 CSP 模块 → 电池的商业证据关卡 → 强化学习多种子重做 → 看板和第二份备忘录。

**局限：**

- 两个回测都只用已发表的数据：电池是一个数据集里的已发表材料，散热是 103 个简单二元化合物的 DFT 参考值。
- 离线的"实验次数"不是实验成本；没有任何一笔投入的真实成本数据。
- 商业证据关卡只用了 28 次检索，按设计不全面；它只回答了四个事先定好的问题。
- 三种角色视角（科学验证、商业策略、S&O）用来组织问题，不代表任何人的意见。

**来源：** `modules/battery/REPORT.md`，`modules/thermal/REPORT.md`，`modules/thermal/COMMERCIAL_EVIDENCE_GATE.md`，`data/thermal/literature_sources.csv`（每条文献的链接和阅读层级）。

---

## English version

Approve two small investments in solid-state electrolytes (curating existing measured data; exploration samples when entering a new chemical family). Defer RL-based material selection and battery-maker partnerships. Move chip cooling to watch: the cooling problem is real, but every buyer-side primary source points to cooling architecture, not new materials.

### Decision request and conclusions

**Request:** use two backtests and one commercial evidence gate to decide which investments in solid-state electrolytes and chip cooling get the next unit of resources. Both directions are judged on the same standard: how far the science is credible, whether buyers want it, and which kind of resource is the constraint.

**Three conclusions:**

1. **Battery: AI's gain must be measured against the chemical-family rule, and interpolation within a doping series inflates the apparent gain.** Fund data first, not more complex selection algorithms.
2. **Chip cooling: on 103 simple binary compounds, the better models rank high-conductivity candidates almost identically, but this does not show that real materials discovery is solved.** Gaps remain between the DFT reference and measurement, and between material and device. The commercial evidence gate established who has the problem, how large it is and how buyers accept a solution; it found no primary evidence for why a new material is needed.
3. **Portfolio: approve only low-cost investments that can be checked quickly; give every other item a checkable condition to continue.** Next is the stability screening and CSP module; the battery commercial evidence gate comes before any conversation with a battery maker.

This is a practice memo built on public data only. Every recommendation is an inference.

### 1. Scientific evidence: how far each backtest goes

Both modules use the same evidence standard: the design is registered before running; baselines include a domain rule, not only random; post-hoc analyses are labelled; an independent agent reviews the work and the fixes are applied.

| Direction | What was done | What it shows | What it does not show |
| --- | --- | --- | --- |
| Solid-state electrolytes | Used 499 measured OBELiX compositions as an offline lab and compared six selection policies by the number of experiments needed to find materials above a research screening threshold of 10⁻³ S/cm | In known chemical families, prior measured data saves far more experiments than the differences between selection algorithms; a "test sulfides first" rule captures most of the gain | Whether transfer to a new family is reliable (it worked for sulfides, failed for oxides, and could not be predicted); whether RL has a stable advantage (one policy trained); the real battery-maker gates |
| Chip cooling | Re-scored all 62 models on Matbench Discovery κ_SRME with independently written code (exact leaderboard match); compared screening metrics, a rule baseline and measured values for 7 materials | On these 103 simple binaries, the better models rank high-conductivity candidates almost identically; the rule misses BAs, the models do not | That real materials discovery is solved (the test set's top 10 sits 25% above rank 11, so it is easy to separate); that the DFT reference matches measurement (6 of 7 materials 10–27% low); that known materials can be built into devices |

**Battery: AI's gain must be compared with the chemical-family rule, and interpolation within a doping series inflates the apparent gain.**

- Finding 5 materials above threshold takes about 30 experiments at random (about a quarter of campaigns do not get there within 40). Screening with a model trained on prior data takes 5 with random folds.
- With whole doping series held out, screening takes 7.6–12.9 experiments and saves only 3–4 more than the chemical-family rule, with overlapping or nearly overlapping intervals (post-hoc).
- An "experiment" in the backtest is reading a published number, not a real cost; the prior data is also treated as free.

**Chip cooling: consistent model rankings do not mean discovery is solved.**

- In the better half of the leaderboard (31 models), 28 give exactly the same top 10. The five best models sit a median 2.9% from the DFT reference.
- A "tetrahedral structure, light atoms" rule finds 6 of the top 10 but ranks BAs 21st; every model with SRME below 0.2 puts BAs in its top 5. Computation adds value where the rule fails.
- Two gaps remain: between the DFT reference and measurement, and between material and device (GaN–diamond interface resistance commonly 20–30 m²K/GW; BAs crystals still millimetre-scale; commercial AlN 216–278 W/m·K against an intrinsic 321).

### 2. Buyer demand: the cooling problem is real, but buyers want cooling architecture, not new materials

Chip cooling went through one commercial evidence gate with exit conditions set in advance: four questions only, primary sources only, at most 30 searches (28 used). Rules and results are in `modules/thermal/COMMERCIAL_EVIDENCE_GATE.md`.

| Question | Result | Primary evidence |
| --- | --- | --- |
| Who has the problem? | Pass | Microsoft, TSMC and Google Cloud each name accelerator cooling as a problem to solve in their own material |
| How big is it? | Pass | AMD MI355X typical board power 1400 W; NVIDIA DGX B200 maximum 1000 W per GPU; H100 SXM is 700 W |
| How do buyers accept a solution? | Pass | OCP cold-plate test specification: case-to-coolant-inlet thermal resistance, measured on a test vehicle with TIM, coolant about 45 °C, at several flow rates; TSMC also uses junction temperature at a stated power and leak rate after reliability tests |
| Why is a new material needed? | Fail | Buyer-side sources all point to cooling architecture: Microsoft microfluidics, Google liquid cooling, TSMC direct-to-silicon cooling that removes the TIM layer. TSMC says TIMs limit cooling, but it compares known materials and aims to remove the layer |

- **The only evidence of payment comes from a supplier.** Akash's own release reports a $27M contract with a cloud provider for diamond-cooled servers; the diamond type and its position are not disclosed, and there is no independent test.
- **No primary source found, so not cited:** TSMC's "package power from 600 W to 4100 W", GB300 power, and the buyer behind Akash's $300M order.
- **Battery demand has not been through the same gate.** 10⁻³ S/cm is a research screening threshold, not a battery-maker standard; buyer-side numbers for later gates (electrochemical window, interfaces) are still missing.

### 3. Resource allocation: approve two small battery investments; defer or watch the rest

The two approvals are both in batteries: curating existing measured data, and exploration samples when entering a new chemical family. Chip cooling moves to watch under the gate's pre-set rules. Near-term commercial impact and long-term scientific value are ranked separately, not merged into one score. Without cost data, no ROI is given.

| Investment | Decision | Rationale | Constraining resource | Continue if | Stop if |
| --- | --- | --- | --- | --- | --- |
| Battery: curate existing measured conductivity data for screening in known families | Approve | In known families, prior data saves far more experiments than algorithm differences | Data | With the new data, a series-held-out backtest still saves experiments against the family rule and the intervals stop overlapping | With the new data, the series-held-out result is still indistinguishable from the family rule |
| Battery: run a small set of exploration samples when entering a new chemical family | Approve (limited scope) | Whether transfer works cannot be predicted: it worked for sulfides, failed for oxides | Lab experiments | The model's ranking matches measurements in the first few experiments; then scale the budget | Rankings disagree: fall back to the family rule or random exploration |
| Battery: RL-based material selection | Defer | One policy trained; no stable advantage | Compute | After a multi-seed rerun, it beats computational screening on the official split, cv5 and the series-grouped split | It fails to beat screening on any split |
| Battery: partnership talks with a battery maker | Defer | The threshold is a research threshold; no buyer numbers for later gates | Partners | Pass a commercial evidence gate in the same format and obtain buyer-side acceptance metrics | The gate finds no buyer-side acceptance metric |
| Cooling: improve general models' κ scores to find thermal materials | Do not fund | Better models already agree, and the test set is too easy to prove anything | Compute | On a harder dataset with complex structures, model rankings diverge | — |
| Cooling: discover new thermal materials | Watch | No primary evidence that buyers need a new material; buyers point to cooling architecture | Compute and lab | A buyer (not a supplier) publicly names a material as the limit and is willing to pay for it | — |
| Cooling: build known high-conductivity materials into devices | Watch | Same as above; the only payment evidence comes from a supplier, with no independent test | Partners | Diamond-cooled servers get an independent test reported as OCP thermal resistance or junction temperature | — |
| Long-term science: physics of the thermal reference calculation (four-phonon, defects, systematic comparison with measurement) | Defer | 6 of 7 materials sit 10–27% below measurement in DFT; would raise trust in computation but does not change near-term decisions | Compute | Restart when chip cooling returns to priority | — |

Directions are not compared by how many gates they have passed: the cooling problem is more certain than the battery one and its acceptance metric is clearer, but the "new material needed" question failed.

### 4. Two return paths in chip cooling: materials discovery vs device validation

Device validation is closer to a return: it uses materials already measured to conduct heat well, and it is stuck on interfaces and sizes that can be measured directly. Discovery is further away: after discovery, the device-validation path still has to be walked. Without reliable cost data, no ROI is computed; the comparison is of remaining gates and where the next piece of information comes from.

|  | Materials discovery | Device validation (known high-conductivity materials) |
| --- | --- | --- |
| When value arrives | A new material beats known ones in a device and passes fabrication, interface, reliability and buyer acceptance | A known material, in the buyer's package, lowers thermal resistance or junction temperature on the buyer's acceptance metric |
| Gates still ahead | Computed candidate → trustworthy reference calculation → synthesis and measurement → growth to usable size → interface and device → buyer acceptance | Interface and device → buyer acceptance |
| Evidence today | On simple binaries, model rankings already agree; no evidence for complex structures. BAs took about 5 years from prediction (2013) to measurement (2018), and its crystals are still millimetre-scale | Interface resistance, wafer size and thermal-expansion mismatch all have measurable numbers; GaN-on-diamond RF devices are on sale |
| Largest unknown | Whether complex structures hold materials easier to make and better at interfaces than known ones | Whether buyers need a materials solution or will solve it with cooling architecture; what their acceptance metric is |
| Cheapest next information | A re-score on a harder thermal-conductivity dataset with complex structures (computation only) | The commercial evidence gate (Section 2, done), then direct conversations with buyers or partners for acceptance metrics |

Both paths rest on one premise: buyers need better heat-spreading materials. The commercial evidence gate found no primary evidence for it; buyers point to cooling architecture. So neither path is a priority now; device validation remains the closer one and should go first if the premise is ever met.

### 5. What would change this recommendation

| If this happens | What changes |
| --- | --- |
| A buyer (not a supplier) publicly names a thermal material as the limit and is willing to pay for it | Cooling moves from watch to candidate investment, starting with device integration of known materials |
| Diamond-cooled servers get an independent test reported as OCP thermal resistance or junction temperature | Same as above |
| On a harder thermal dataset with complex structures, model rankings diverge | Improving model accuracy becomes a meaningful compute investment again |
| After a multi-seed rerun, RL beats computational screening on every split | RL selection moves from defer to a small pilot |
| The battery commercial evidence gate obtains buyer-side acceptance metrics | Joint exploration with a battery maker becomes possible, with milestones set on those metrics |

**Next steps (by dependency):** stability screening and CSP module → battery commercial evidence gate → multi-seed RL rerun → portfolio board and the second memo.

**Limits:**

- Both backtests use published data only: for batteries, published materials in one dataset; for cooling, DFT reference values for 103 simple binaries.
- Offline "experiment counts" are not experiment costs; there is no real cost data for any investment.
- The commercial evidence gate used 28 searches and is incomplete by design; it answers only four pre-set questions.
- The three role lenses (scientific validation, commercial strategy, S&O) organise the questions; they do not represent anyone's views.

**Sources:** `modules/battery/REPORT.md`, `modules/thermal/REPORT.md`, `modules/thermal/COMMERCIAL_EVIDENCE_GATE.md`, `data/thermal/literature_sources.csv` (link and read level for every source).
