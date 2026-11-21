# 芯片散热：商业证据关卡（Commercial Evidence Gate）

> 登记于 2026-11-21，在做任何检索之前写下。第一版只有三个问题；同日、仍在检索之前，按"谁有这个问题、问题有多大、用什么指标验收、为什么需要新材料"改成下面四个问题。这不是一轮行业调研：只回答这四个问题，只认一手来源，到预算或问完就停。结果写在文末，规则不再改。

## 为什么要过这一关

散热模块的计算结果只说明：在 103 个简单二元化合物上，较好的模型对高导热候选的排序高度一致。这不证明真实的材料发现问题已经解决，也不说明有人需要新材料。决策建议还缺需求侧的一手证据，而现有的需求侧条目大多是二手转述（`data/thermal/literature_sources.csv` 中 T056、T057、T061–T063）。

## 四个问题

| 编号 | 问题 | 过关标准 |
|---|---|---|
| Q1 | 谁有这个问题？ | 至少两家买家一侧的机构（芯片厂、代工厂、云厂商），在自己发布的材料里说数据中心加速器的散热是需要解决的问题。微软（T060）已经是一手，算一家 |
| Q2 | 问题有多大？ | 芯片厂商自己的规格页或数据表，给出当前一代数据中心加速器的功耗（TDP 或板卡功耗），高于 H100 SXM 的 700 W（T055）；或代工厂自己发布的封装功率预测 |
| Q3 | 他们用什么指标验收？ | 买家一侧或标准组织自己发布的验收指标：例如结温上限、结到冷却液的热阻、可靠性测试条件。只要能说清"用什么量、在什么条件下测"即可，不要求具体阈值 |
| Q4 | 为什么需要新的材料方案？ | 买家一侧的一手说法，指出现有材料或界面层（导热界面材料、封装盖、散热片材料）是限制，需要更好的材料；或者买家为高导热散热材料付钱（买家自己说，或供应商说且点名买家）。如果买家一侧把方向放在冷却架构（例如微流体、直接液冷）而不是材料上，照实记录 |

## 规则

- **只认一手来源：** 公司自己的网站、新闻稿、投资者材料、产品规格页和数据表；公司作者的会议或期刊论文（出版方页面或摘要页）；标准组织自己的页面。行业媒体、分析师报告、博客和搜索摘要都不算。
- **不加新主题：** 只复核已有条目（T033、T034、T056、T057、T060–T063），以及为回答 Q1–Q4 所必需的同类一手来源。
- **预算：** 最多 30 次检索或打开网页。用完即停，没查到的记为"未找到一手来源"。
- **每条的停止规则：** 查过公司新闻室、相关产品页或论文出版方页面仍没有，就记"未找到一手来源"，不用二手来源顶替。
- **执行方式：** 由一个研究代理执行。我核对它给出的链接和原文摘录，不扩展范围。

## 结果怎么用（事先定好）

| 结果 | 备忘录里怎么写 | 散热方向的建议 |
|---|---|---|
| Q1、Q2 过 | 问题和规模有一手依据 | 散热问题本身可以作为投资前提 |
| Q1 或 Q2 不过 | 需求侧证据：未核实 | 散热相关投入暂缓；下一道关卡是和买家或伙伴的直接对话，不再做桌面调研 |
| Q3 过 | 写明验收指标，后续的器件验证按这个量设计 | — |
| Q3 不过 | 写明"验收指标未知" | 任何器件验证投入之前，先从伙伴处拿到验收指标 |
| Q4 过（材料是限制，或有买家付费） | 写明依据 | 器件化已知材料可作为工作假设；发现新材料仍需单独证据 |
| Q4 不过，或买家一侧指向冷却架构 | 写明"没有一手证据表明买家需要新材料" | 材料发现和材料器件化都不作为优先投入；散热方向在备忘录里降为观察 |

不管结果如何，关卡结束后进入稳定性筛选与 CSP 模块。

## 结果（2026-11-21）

研究代理用了 30 次预算中的 28 次。我打开四个页面核对了引文，都与原文一致：AMD ROCm 文档、Google Cloud 博客、TSMC 的 ECTC 2025 论文页、Akash 新闻室。新找到的一手来源加进了 `data/thermal/literature_sources.csv`，编号 G001–G007。

| 问题 | 结论 | 依据 |
|---|---|---|
| Q1 谁有这个问题 | **过** | 三家买家一侧的机构在自己的材料里说了：微软（T060）、TSMC（G002，G005）、Google Cloud（G001） |
| Q2 问题有多大 | **过** | AMD MI355X 板卡功耗 1400 W，MI350X 1000 W（G003）；NVIDIA DGX B200 每颗 GPU 最大 1000 W（G004）；都高于 H100 SXM 的 700 W |
| Q3 用什么指标验收 | **过** | OCP 冷板测试规范：热阻 R = (壳温 − 冷却液入口温度) / 功率，在带导热界面材料的处理器或测试芯片上测，冷却液约 45 °C，多个流量（G006）。TSMC 另用给定功率下的结温，以及回流焊、温度循环、高温存储后的漏率（G002，G005） |
| Q4 为什么需要新材料 | **不过**（买家一侧指向冷却架构） | 见下 |

**Q4 的细节。**
- **买家一侧都指向冷却架构，不是新材料。** 微软走微流体，Google 走液冷，TSMC 走去掉导热界面层的直接液冷。TSMC 说导热界面材料"限制散热效果"（G005），但它比较的是已知材料（石墨、液态金属、铟），给出的方向是把这一层去掉（G002）。
- **"有人付钱"只在字面上满足。** Akash 自己的新闻稿点名了一个买家：与 NxtGen 签了 2700 万美元的金刚石散热服务器合同（G007）。但这是整机服务器合同，金刚石的类型和在封装里的位置都没公开，也没有独立测试。另一笔 3 亿美元的订单（T034）仍没点名买家。
- **按事先定好的规则：** 买家一侧指向冷却架构，所以记为"没有一手证据表明买家需要新材料"。

**没找到一手来源的：** TSMC 在 SEMICON Taiwan 2026 说的"封装功率 600 W 到 4100 W"（T061）及对应的界面材料原话（T062）；0.055 °C/W（T063，不在论文摘要里）；GB300/B300 的功耗（T057）；3 亿美元订单的买家（T034）。这些在备忘录里不引用。

**按规则得出的处理：**
- 散热问题本身（Q1、Q2）有一手依据，验收指标（Q3）已知。后续任何器件验证，都按"壳到冷却液的热阻、给定功率下的结温、可靠性测试后的漏率"来设计。
- 材料发现和材料器件化都不作为优先投入，散热方向在备忘录里降为**观察**。
- **会让这个结论改变的信号：** 一个买家（不是供应商）公开说某种材料是限制并愿意为它付钱；或金刚石散热服务器有独立测试结果。

关卡到此结束，不再做桌面调研。下一步进入稳定性筛选与 CSP 模块。

---

## English version

### Chip cooling: commercial evidence gate

> Registered on 2026-11-21, written before any search. The first version had only three questions. On the same day, still before any search, it was changed to the four questions below, following "who has this problem, how big is the problem, what metric is used for acceptance, why new materials are needed". This is not a round of industry research: it answers only these four questions, accepts only primary sources, and stops when the budget runs out or the questions are answered. The results are written at the end, and the rules do not change.

### Why this gate

The computational results of the thermal module only show that, on 103 simple binary compounds, the better models rank the high-thermal-conductivity candidates in a highly consistent order. This does not prove that the real materials discovery problem is solved, and it does not show that anyone needs new materials. The decision recommendations still lack primary-source evidence from the demand side, and the existing demand-side entries are mostly secondhand retellings (T056, T057, T061–T063 in `data/thermal/literature_sources.csv`).

### Four questions

| ID | Question | Pass criterion |
|---|---|---|
| Q1 | Who has this problem? | At least two buyer-side organizations (chipmakers, foundries, cloud providers) say in their own published material that cooling of data-center accelerators is a problem to be solved. Microsoft (T060) is already a primary source and counts as one |
| Q2 | How big is the problem? | A chipmaker's own spec page or datasheet giving the power (TDP or board power) of a current-generation data-center accelerator above the 700 W of the H100 SXM (T055); or a package power projection published by a foundry itself |
| Q3 | What metric do they use for acceptance? | An acceptance metric published by the buyer side or a standards body itself: for example a junction temperature limit, junction-to-coolant thermal resistance, or reliability test conditions. It is enough to state "what quantity, measured under what conditions"; specific thresholds are not required |
| Q4 | Why is a new materials solution needed? | A primary buyer-side statement that existing materials or interface layers (thermal interface materials, package lids, heat spreader materials) are a limit and better materials are needed; or buyers paying for high-thermal-conductivity cooling materials (said by the buyer, or by a supplier who names the buyer). If the buyer side puts its direction on cooling architecture (for example microfluidics or direct liquid cooling) rather than materials, record that as it is |

### Rules

- **Primary sources only:** companies' own websites, press releases, investor materials, product spec pages and datasheets; conference or journal papers by company authors (publisher page or abstract page); standards bodies' own pages. Trade media, analyst reports, blogs and search snippets do not count.
- **No new topics:** only re-check existing entries (T033, T034, T056, T057, T060–T063), plus primary sources of the same kind that are needed to answer Q1–Q4.
- **Budget:** at most 30 searches or page opens. Stop when it is used up; anything not found is recorded as "no primary source found".
- **Stop rule for each item:** if the company newsroom, the relevant product page or the paper's publisher page has been checked and there is still nothing, record "no primary source found". Do not substitute a secondhand source.
- **How it is run:** by one research agent. I check the links and original-text excerpts it gives, and do not extend the scope.

### How the results are used (set in advance)

| Result | What the memo says | Recommendation for the thermal direction |
|---|---|---|
| Q1 and Q2 pass | The problem and its scale have primary-source support | The cooling problem itself can serve as an investment premise |
| Q1 or Q2 fails | Demand-side evidence: not verified | Pause thermal-related investment; the next gate is a direct conversation with buyers or partners, no more desk research |
| Q3 passes | State the acceptance metric; later device validation is designed around this quantity | — |
| Q3 fails | State "acceptance metric unknown" | Before any investment in device validation, first get the acceptance metric from a partner |
| Q4 passes (materials are a limit, or a buyer pays) | State the basis | Device integration of known materials can serve as a working hypothesis; discovering new materials still needs separate evidence |
| Q4 fails, or the buyer side points to cooling architecture | State "no primary-source evidence that buyers need new materials" | Neither materials discovery nor materials device integration is a priority investment; the thermal direction is downgraded to watch in the memo |

Whatever the result, after the gate the work moves on to the stability screening and CSP module.

### Results (2026-11-21)

The research agent used 28 of the budget of 30. I opened four pages to check the quotations, and all matched the original text: the AMD ROCm documentation, a Google Cloud blog post, TSMC's ECTC 2025 paper page, and the Akash newsroom. The newly found primary sources were added to `data/thermal/literature_sources.csv` as G001–G007.

| Question | Conclusion | Basis |
|---|---|---|
| Q1 Who has this problem | **Pass** | Three buyer-side organizations said so in their own material: Microsoft (T060), TSMC (G002, G005), Google Cloud (G001) |
| Q2 How big is the problem | **Pass** | AMD MI355X board power 1400 W, MI350X 1000 W (G003); NVIDIA DGX B200 up to 1000 W per GPU (G004); all above the 700 W of the H100 SXM |
| Q3 What acceptance metric | **Pass** | OCP cold plate test specification: thermal resistance R = (case temperature − coolant inlet temperature) / power, measured on a processor or test chip with thermal interface material, coolant at about 45 °C, at several flow rates (G006). TSMC also uses junction temperature at a given power, and leak rate after reflow, temperature cycling and high-temperature storage (G002, G005) |
| Q4 Why new materials are needed | **Fail** (the buyer side points to cooling architecture) | See below |

**Q4 details.**
- **The buyer side all points to cooling architecture, not new materials.** Microsoft takes microfluidics, Google takes liquid cooling, and TSMC takes direct liquid cooling that removes the thermal interface layer. TSMC says thermal interface materials "limit cooling performance" (G005), but it compares known materials (graphite, liquid metal, indium), and the direction it gives is to remove this layer (G002).
- **"Someone pays" is met only literally.** Akash's own press release names a buyer: a USD 27 million contract with NxtGen for diamond-cooled servers (G007). But this is a whole-server contract. The diamond type and its position in the package are not disclosed, and there is no independent test. Another order of USD 300 million (T034) still names no buyer.
- **Under the rule set in advance:** the buyer side points to cooling architecture, so this is recorded as "no primary-source evidence that buyers need new materials".

**No primary source found for:** TSMC's "package power from 600 W to 4100 W" at SEMICON Taiwan 2026 (T061) and the matching original wording on interface materials (T062); 0.055 °C/W (T063, not in the paper abstract); the power of GB300/B300 (T057); the buyer of the USD 300 million order (T034). These are not cited in the memo.

**What follows under the rules:**
- The cooling problem itself (Q1, Q2) has primary-source support, and the acceptance metrics (Q3) are known. Any later device validation is designed around "case-to-coolant thermal resistance, junction temperature at a given power, and leak rate after reliability tests".
- Neither materials discovery nor materials device integration is a priority investment; the thermal direction is downgraded to **watch** in the memo.
- **Signals that would change this conclusion:** a buyer (not a supplier) says publicly that a material is a limit and is willing to pay for it; or diamond-cooled servers get independent test results.

The gate ends here, with no more desk research. The next step is the stability screening and CSP module.
