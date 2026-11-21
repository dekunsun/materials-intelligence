# 固态电池电解质：商业证据关卡（Commercial Evidence Gate）

> 登记于 2026-11-21，在做任何检索之前写下。格式和芯片散热的关卡相同。这不是一轮行业调研：只回答下面四个问题，只认一手来源，到预算或问完就停。结果写在文末，规则不再改。

## 为什么要过这一关

电池模块的回测用了 10⁻³ S/cm 作为"过线"标准，但它只是研究筛选阈值，没有买家侧出处。电芯级的门槛（700 次循环、容量损失不超过 20%）和样品周期（A 样到 B1 样约两年）来自系列文章，没有核实。投资备忘录 v2 把"和电池厂谈合作"暂缓，继续条件是：同格式的关卡拿到买家侧的验收指标。

## 四个问题

| 编号 | 问题 | 过关标准 |
|---|---|---|
| Q1 | 谁有这个问题？ | 至少两家买家一侧的机构（电芯厂、车厂），在自己发布的材料里说固态电池或固态电解质是在做的开发目标 |
| Q2 | 问题有多大？ | 买家一侧自己发布的量化计划：量产或中试的时间、产能、装车目标，任选其一，有数字 |
| Q3 | 他们用什么指标验收？ | 买家一侧或标准组织自己发布的验收指标：电芯级（循环次数和容量保持、能量密度、倍率、温度范围）或电解质级（离子电导率、电化学窗口、空气稳定性）。说清"用什么量、在什么条件下"即可。**另外单独记录：** 10⁻³ S/cm 这类电导率门槛有没有买家侧出处；学术界的基准（例如 Randau et al. 2020）只作为背景记录，不算过关 |
| Q4 | 为什么需要新的电解质材料？ | 买家一侧的一手说法，指出现有电解质材料是限制（电导率、稳定性、界面、可制造性），需要新材料或新的材料伙伴；或者买家为固态电解质材料付钱（买家自己说，或供应商说且点名买家）。如果买家一侧把瓶颈放在制造、良率或成本上而不是材料上，照实记录 |

## 规则

- **只认一手来源：** 公司自己的网站、新闻稿、投资者材料（年报、股东信、财报电话会文字稿）、产品规格页；公司作者的论文（出版方页面或摘要页）；标准组织自己的页面。行业媒体、分析师报告、博客和搜索摘要都不算。
- **只复核已有条目，不加新主题：** 系列文章的三条说法（电芯级门槛、样品周期、"一种电解质做出来但电导率远低于门槛"），以及为回答 Q1–Q4 所必需的同类一手来源。
- **预算：** 最多 30 次检索或打开网页。用完即停，没查到的记为"未找到一手来源"。
- **每条的停止规则：** 查过公司新闻室、投资者材料或出版方页面仍没有，就记"未找到一手来源"，不用二手来源顶替。
- **执行方式：** 由一个研究代理执行；我核对它给出的链接和原文摘录，不扩展范围。

## 结果怎么用（事先定好）

| 结果 | 备忘录和看板里怎么写 | 对决策的影响 |
|---|---|---|
| Q1、Q2 过 | 问题和规模有一手依据 | 固态电解质可以作为投资前提 |
| Q1 或 Q2 不过 | 需求侧证据：未核实 | 电池方向的所有外部投入暂缓，只保留已批准的两笔内部小投入 |
| Q3 过 | 写明验收指标；回测和后续实验按这些量设计 | "和电池厂谈合作"从暂缓改为**批准（限定范围）**：只谈联合探索，里程碑按这些指标设 |
| Q3 不过 | 写明"买家侧验收指标未知" | 触发备忘录 v2 的停止条件：合作谈判不做；继续内部工作 |
| Q4 过（材料是限制，或有买家付费） | 写明依据 | 用 AI 筛选新电解质有买家拉动；先验数据和探索性样本两笔投入保持 |
| Q4 不过，或买家一侧把瓶颈放在制造、良率、成本上 | 写明"没有一手证据表明买家需要新电解质材料" | 新电解质发现降为观察；已批准的两笔内部小投入保留（它们服务于筛选效率，不依赖新材料需求），但不扩大 |
| 10⁻³ S/cm 找到买家侧出处 | 写明出处 | 回测的阈值改称"买家侧阈值" |
| 没找到 | 维持"研究筛选阈值"的说法 | 不变 |

不管结果如何，关卡结束后不再做桌面调研。

## 结果（2026-11-21）

研究代理用了 30 次预算中的 28 次。我打开四个页面核对了引文，都与原文一致：大众（PowerCo）关于 QuantumScape 耐久测试的新闻稿、宝马关于 Solid Power 和三星 SDI 的新闻稿、丰田与出光的新闻稿、三星 SDI 的新闻页。一手来源记在 `data/battery/literature_sources.csv`，编号 B001–B013。

| 问题 | 结论 | 依据 |
|---|---|---|
| Q1 谁有这个问题 | **过** | 丰田、三星 SDI、大众（PowerCo）、宝马都在自己的新闻稿里把全固态电池列为在做的开发目标（B001、B003、B004、B009） |
| Q2 问题有多大 | **过** | 三星 SDI 计划 2027 年量产，能量密度 900 Wh/L（B003）；丰田与出光目标 2027 或 2028 年商业化（B001）；PowerCo 获授权最多每年 40 GWh，可选扩到 80 GWh（B004） |
| Q3 用什么指标验收 | **过（有保留）** | 大众称"这一开发阶段的行业标准目标是 700 次充电循环、容量损失不超过 20%"，但没写温度和倍率等测试条件（B005）。美国汽车厂联盟 USABC 的电芯目标写了条件：300 Wh/kg、700 Wh/L、1,000 次 DST 循环、30 °C 下 10 分钟快充到 80%、−30 到 +65 °C；但这是通用电动车目标，不专门针对固态（B007）。USABC 是汽车厂联盟，不是正式的标准组织 |
| Q4 为什么需要新的电解质材料 | **过（混合）** | 丰田说"最大的挑战是耐久性"，反复充放电会在正负极和固态电解质之间产生裂纹，并和出光自 2013 年起合作开发抗裂的电解质（B002）。宝马的新闻稿说 Solid Power 将向三星 SDI 供应硫化物固态电解质（B009），但没写付款。同时，大众说下一步是"完善并放大制造工艺"（B006）。买家一侧既点名了材料和界面，也点名了制造 |

**电导率门槛：没有找到买家侧出处。** 只找到供应商一侧的数字：Solid Power 的硫银锗矿粉末规格是 25 °C 下大于 5.0、3.25、1.5 mS/cm（B010，投资者材料；对应哪一代是从表格列的顺序推断的）。USABC 的活性材料目标里没有电解质或电导率的指标（B008）。按规则，10⁻³ S/cm 继续叫"研究筛选阈值"。

**系列文章的三条说法：**
- **电芯级门槛（700 次循环、容量损失不超过 20%）：** 找到一手来源，是大众的新闻稿（B005）；但它是"这一开发阶段的行业标准目标"，不是正式的验收规范，也没有测试条件。
- **QuantumScape 从 A 样到 B1 样约两年：** 需要修正。一手来源显示 A0 样品 2022 年发出（B012），B1 样品 2025 年第三季度开始发出（B011），约 2.5–2.8 年；B0 的日期没有核实。
- **"一种筛选出的电解质做出来了，电导率远低于门槛"：** 找到一手来源，是微软和 PNNL 的预印本：AI 筛选出的 Na₂LiYCl₆ 在 100 °C 下电导率 2.2×10⁻⁶ S/cm（B013），比 10⁻³ S/cm 低约三个数量级。"系列文章指的就是这篇"是推断。

**没找到一手来源的：** 买家侧的电导率门槛；大众 700 次循环目标的测试条件；有具名买家为固态电解质材料付钱的说法；QuantumScape 2022 年第四季度股东信（投资者网站返回 403，改用了 SEC 上的年报）。学术基准（Randau 2020；Bielefeld、Weber、Janek 2020）没有打开，什么也没记录。

**按规则得出的处理：**
- Q1、Q2 过：固态电解质可以作为投资前提。
- Q3 过：**"和电池厂谈合作"从暂缓改为批准（限定范围）**，只谈联合探索，里程碑按买家侧的电芯级指标设：先用大众的 700 次循环、容量损失不超过 20%，测试条件要在谈判中补齐。要注意，这些都是电芯级指标；本项目的回测只到电导率这一步，从电导率到电芯级循环之间，需要伙伴的电芯工程能力。
- Q4 按标准算过，但买家点名的材料限制是**界面耐久性（裂纹）**，不是电导率；而本模块的回测只衡量电导率。所以已批准的两笔内部小投入保留；"为提高电导率而扩大筛选"不扩大；界面稳定性是下一个需要证据的关卡。
- 10⁻³ S/cm 维持"研究筛选阈值"的说法。

关卡到此结束，不再做桌面调研。

---

## English version

### Solid-state battery electrolytes: Commercial Evidence Gate

> Registered on 2026-11-21, before any search. Same format as the chip-cooling gate. This is not an industry survey: it answers only the four questions below, accepts only primary sources, and stops at the budget or when the questions are answered. Results go at the end; the rules do not change.

#### Why this gate

The battery backtest used 10⁻³ S/cm as its "above threshold" bar, but that is only a research screening threshold with no buyer-side source. The cell-level threshold (700 cycles with at most 20% capacity loss) and the sample cycle (about two years from A sample to B1 sample) come from the series article and are unverified. Investment Decision Memo v2 deferred "partnership talks with a battery maker"; the condition to continue is that a gate in the same format obtains buyer-side acceptance metrics.

#### Four questions

| ID | Question | Pass criterion |
|---|---|---|
| Q1 | Who has the problem? | At least two buyer-side organisations (cell makers, carmakers) say, in their own published material, that solid-state batteries or solid-state electrolytes are a development goal they are working on |
| Q2 | How big is it? | A quantified plan published by the buyer side itself: a date, capacity or vehicle target for mass production or a pilot line, any one, with a number |
| Q3 | Which metrics do they use for acceptance? | Acceptance metrics published by the buyer side or a standards body itself: cell level (cycle count and capacity retention, energy density, rate, temperature range) or electrolyte level (ionic conductivity, electrochemical window, air stability). Naming "which quantity, under which conditions" is enough. **Recorded separately:** whether a conductivity threshold such as 10⁻³ S/cm has a buyer-side source; academic benchmarks (for example Randau et al. 2020) are recorded as context only and do not pass |
| Q4 | Why are new electrolyte materials needed? | A buyer-side primary statement that current electrolyte materials are the limit (conductivity, stability, interfaces, manufacturability) and that new materials or new material partners are needed; or a buyer paying for solid-electrolyte materials (the buyer says so, or a supplier says so and names the buyer). If the buyer side places the bottleneck in manufacturing, yield or cost rather than materials, record that faithfully |

#### Rules

- **Primary sources only:** the company's own website, press releases, investor material (annual reports, shareholder letters, earnings-call transcripts), product specification pages; company-authored papers (publisher or abstract page); a standards body's own pages. Trade press, analyst reports, blogs and search snippets do not count.
- **Re-check existing items only; no new topics:** the series article's three claims (cell-level threshold, sample cycle, "one electrolyte made but conductivity far below threshold"), plus same-kind primary sources needed to answer Q1–Q4.
- **Budget:** at most 30 searches or page opens. Stop when used up; anything not found is recorded as "no primary source found".
- **Per-item stopping rule:** after checking the company newsroom, investor material or publisher page without success, record "no primary source found"; do not substitute a secondary source.
- **Execution:** run by one research agent; I check the links and quotes it returns and do not widen the scope.

#### How results are used (fixed in advance)

| Result | What the memo and board say | Effect on decisions |
|---|---|---|
| Q1 and Q2 pass | The problem and its scale have primary support | Solid-state electrolytes can serve as an investment premise |
| Q1 or Q2 fails | Demand-side evidence: unverified | All external battery investments deferred; only the two approved small internal investments remain |
| Q3 passes | State the acceptance metrics; backtests and later experiments are designed around them | "Partnership talks with a battery maker" moves from defer to **approve (limited scope)**: joint exploration only, milestones set on those metrics |
| Q3 fails | State "buyer-side acceptance metrics unknown" | Triggers Memo v2's stop condition: no partnership talks; internal work continues |
| Q4 passes (materials are the limit, or a buyer pays) | State the evidence | AI screening for new electrolytes has buyer pull; the prior-data and exploration-sample investments are kept |
| Q4 fails, or the buyer side places the bottleneck in manufacturing, yield or cost | State "no primary evidence that buyers need new electrolyte materials" | New-electrolyte discovery moves to watch; the two approved internal investments stay (they serve screening efficiency and do not depend on demand for new materials) but are not expanded |
| A buyer-side source for 10⁻³ S/cm is found | State the source | The backtest threshold is renamed a "buyer-side threshold" |
| Not found | Keep calling it a "research screening threshold" | No change |

Whatever the result, no further desk research follows this gate.

#### Results (21 November 2026)

The research agent used 28 of its 30-search budget. I opened four pages and checked the quotes; all match the original text: Volkswagen's (PowerCo) release on the QuantumScape endurance test, BMW's release on Solid Power and Samsung SDI, the Toyota–Idemitsu release, and Samsung SDI's news page. Primary sources are recorded in `data/battery/literature_sources.csv`, IDs B001–B013.

| Question | Result | Evidence |
|---|---|---|
| Q1 Who has the problem? | **Pass** | Toyota, Samsung SDI, Volkswagen (PowerCo) and BMW each list all-solid-state batteries as a development goal in their own releases (B001, B003, B004, B009) |
| Q2 How big is it? | **Pass** | Samsung SDI plans mass production in 2027 at 900 Wh/L (B003); Toyota and Idemitsu target commercialisation in 2027 or 2028 (B001); PowerCo is licensed for up to 40 GWh a year, with an option for 80 GWh (B004) |
| Q3 Which acceptance metrics? | **Pass (with caveats)** | Volkswagen says "the industry-standard targets for this development phase are 700 charging cycles and a maximum capacity loss of 20 percent", but gives no test conditions such as temperature or C-rate (B005). The US carmakers' consortium USABC gives cell targets with conditions: 300 Wh/kg, 700 Wh/L, 1,000 DST cycles, a 10-minute fast charge to 80% at 30 °C, −30 to +65 °C; but these are generic EV targets, not specific to solid state (B007). USABC is a carmaker consortium, not a formal standards body |
| Q4 Why are new electrolyte materials needed? | **Pass (mixed)** | Toyota says "the biggest challenge is durability": repeated charging and discharging causes cracks between the electrodes and the solid electrolyte, and it has worked with Idemitsu since 2013 on a crack-resistant electrolyte (B002). BMW's release says Solid Power will supply sulfide solid electrolyte to Samsung SDI (B009), but states no payment. At the same time, Volkswagen says the next step is to "perfect and scale the manufacturing processes" (B006). The buyer side names both materials and interfaces, and manufacturing |

**Conductivity threshold: no buyer-side source found.** Only supplier-side numbers were found: Solid Power's argyrodite powder specs are above 5.0, 3.25 and 1.5 mS/cm at 25 °C (B010, investor material; which generation each value belongs to is inferred from column order). USABC's active-material targets set no electrolyte or conductivity target (B008). Under the rules, 10⁻³ S/cm stays a "research screening threshold".

**The series article's three claims:**
- **Cell-level threshold (700 cycles, at most 20% capacity loss):** primary source found, a Volkswagen release (B005); but it is "the industry-standard target for this development phase", not a formal acceptance specification, and has no test conditions.
- **QuantumScape about two years from A sample to B1 sample:** needs correcting. Primary sources show A0 samples shipped in 2022 (B012) and B1 samples began shipping in Q3 2025 (B011), about 2.5–2.8 years; the B0 date was not verified.
- **"A screened electrolyte was made, with conductivity far below the threshold":** primary source found, a Microsoft and PNNL preprint: the AI-screened Na₂LiYCl₆ measured 2.2×10⁻⁶ S/cm at 100 °C (B013), about three orders of magnitude below 10⁻³ S/cm. That the series article refers to this paper is an inference.

**No primary source found:** a buyer-side conductivity threshold; test conditions for Volkswagen's 700-cycle target; a named buyer paying for solid-electrolyte material; QuantumScape's Q4 2022 shareholder letter (its investor sites returned 403; the SEC annual report was used instead). The academic benchmarks (Randau 2020; Bielefeld, Weber, Janek 2020) were not opened, and nothing was recorded from them.

**What the rules give:**
- Q1 and Q2 pass: solid-state electrolytes can serve as an investment premise.
- Q3 passes: **"partnership talks with a battery maker" moves from defer to approve (limited scope)**, joint exploration only, with milestones set on buyer-side cell-level metrics: start from Volkswagen's 700 cycles with at most 20% capacity loss, and settle the test conditions in the talks. Note that these are cell-level metrics; this project's backtest only reaches conductivity, and getting from conductivity to cell-level cycling needs a partner's cell-engineering capability.
- Q4 passes on its criterion, but the material limit the buyer names is **interface durability (cracking)**, not conductivity, while this module's backtest measures only conductivity. So the two approved small internal investments stay; screening is not expanded for the sake of higher conductivity; interface stability is the next gate that needs evidence.
- 10⁻³ S/cm keeps the name "research screening threshold".

The gate ends here; no further desk research follows.
