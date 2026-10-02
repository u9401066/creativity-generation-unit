# 哲學後設探究 × 創意：導入 Agent 的框架（討論稿）

> **狀態**：討論稿 v1｜**日期**：2026-10-02｜**前置文件**：[CGU 嚴格審查](./critical-review-and-improvement-plan.md)
>
> **起點**：使用者與 Gemini 討論出的「哲學導入 agent」框架（§1）。本文件做四件事：
> 1. 評估該框架；
> 2. 回答「抽象的高階創意討論，是否本來就屬於哲學」；
> 3. 擴充哲學工具箱；
> 4. 把哲學方法轉成 CGU 可實作的設計。
>
> **寫法**：
> - 把框架**套用在框架自己身上**（§3.2），也套用在 CGU 與上一份審查上（§4.5）。
> - 標記沿用審查文件：【文獻】表示有出處；【推論】表示待驗證。
> - 本文件不含程式碼修改。
>
> **後續**：落地方式見[執行計畫](./program-plan.md)（P3 哲學層；以 Agent Plugins 1.0 交付 skills 與 MCP）。評估 baseline 一律稱 `BL0`–`BL3`，以免與審查缺陷 `B1`–`B11` 混淆。

## 目錄

1. 原始框架摘要
2. 摘要
3. 評估原始框架
4. 抽象的高階創意討論，本來就是哲學範疇嗎？
5. 擴充的哲學工具箱
6. 修訂版框架
7. 導入 CGU 的設計
8. 回到最初的四個問題
9. 待討論決策點（Q11–Q15）
- 附錄：參考文獻

---

## 1. 原始框架摘要

| 部分 | 內容 |
|---|---|
| 哲學的本質 | 不是累積領域事實，而是對「不證自明的前提」做後設審查，並重構概念邊界。科學問「現象如何發生」，技術問「如何有效達成目標」，哲學問「地基底下的地質構造」 |
| 三個核心動作 | ① 剝離隱性預設 ② 界定概念邊界 ③ 整合相容視野（引 Sellars：理解事物如何彼此關聯） |
| 四個提問透鏡 | 概念（我們談的是同一件事嗎？）、知識論（我們憑什麼確信？）、本體論（最小的不可化約實體是什麼？）、規範（目標的正當性從何而來？） |
| 三個場景 | 技術與工具決策、組織與策略規劃、專業判斷與倫理：把操作性問題拉升為結構性問題 |
| 溯源檢驗 | 定義追問 → 反例探尋 → 基礎回溯 → 體系自洽 |
| 價值主張 | 防止用極高的效率，去精準地解決完全錯誤的問題 |

---

## 2. 摘要

1. **框架的核心是對的。** 哲學的價值在於把問題從內容層拉到結構層，防止「精準解決錯誤的問題」——也就是組織科學所說的「第三類錯誤」（Mitroff & Featheringham 1974）。
2. **但它是分析哲學的自畫像，有五個盲點：**
   - 只有批判、沒有生成：漏掉了 Peirce 的溯因（他稱之為「唯一能引入新想法的邏輯操作」），也漏掉了 Deleuze 的「哲學是創造概念」。
   - 地基隱喻預設了基礎論：Neurath／Quine 的「船」與「信念之網」更貼切，也更可操作。
   - 把清晰與一致當成永遠的好事：但在創意中，模糊與矛盾常常是資源。
   - 沒有停損規則：懷疑沒有預算，就會無限回溯。
   - 沒有品質控制：LLM 最擅長產出「聽起來很深、卻不改變任何決定」的問題。
3. **高階創意討論「部分」屬於哲學。**
   - 創意是什麼、對誰算新、價值由誰定義、能否機械化——這些是哲學問題。
   - 如何產生、如何量測、如何實作——這些屬於心理學、計算與設計。
   - 兩者共享一個核心操作：**改變可能性空間的框架**。
4. **一個統一的三層模型：**
   - L0 內容：在框架內解題。
   - L1 框架：目標、假設、概念、隱喻、評估準則。
   - L2 後設框架：選擇框架的規範。

   Boden 的變革型創意、Kuhn 的典範轉移、Schön 的問題設定、洞察研究中的限制鬆綁，全都是「L1 的改變」。哲學擅長**表徵與評估** L1；創意擅長**生成** L1 與 L0。
5. **上一份審查本身就是應用哲學。** 40 項缺陷中最根本的幾項，正好落在框架的四個透鏡上：A1 概念混淆、A5 新穎是相對於誰、C1 沒有測量程序的數字、B8 評分偏好保守。
6. **修訂版框架**由三部分組成：
   - 五個動作：浮現 → 澄清／工程 → 生成 → 檢驗 → 整合或並存。
   - 七個透鏡：原本四個，加上實用後果、系譜、美學。
   - 一個節制原則：懷疑的經濟學——何時升到 L1、質疑哪個假設、何時停。
7. **導入 CGU 的做法：**
   - 讓「框架」成為一等公民物件；把哲學方法實作為「框架算子」。
   - 從模型的典型答案**反推**隱性框架，再改寫框架——以「有理由的新穎」取代「只在 embedding 空間推遠」。
   - 以「改寫了哪個框架元素」作為品質多樣性搜尋的格子維度。
8. **給人類的回饋。** agent 最好的哲學角色是產婆與「另一個視域」：給框架與問題，而不只給答案。但要用「是否改變了決定」與「人是否保有能力」來檢驗，並坦承 Kumar et al.（2025）的反證。

---

## 3. 評估原始框架

### 3.1 做對了什麼

| 主張 | 評價 |
|---|---|
| 哲學是後設審查，而非累積事實 | 與 Wittgenstein「哲學不是一套學說，而是一種活動」（《邏輯哲學論》4.112）一致；把哲學定位為「方法」，對 agent 設計很有用 |
| 三個動作 | 對應分析哲學的三項核心工作：前提分析、概念分析、系統建構；Sellars 的引文正確（1962） |
| 四個透鏡 | 對應哲學的經典分支（語意與概念、知識論、形上學、倫理與價值論），作為檢查清單，涵蓋面廣 |
| 「防止精準解決錯誤的問題」 | 即第三類錯誤，這是哲學導入 agent 最有力的理由 |
| 三個場景的提問演化 | 示範了從內容層到結構層的拉升。例如「承擔 5% 錯誤的人與享受效率的人是否為同一主體」，就是一個很好的規範提問 |

### 3.2 用框架檢驗框架自己

把溯源檢驗的四步套用在框架本身：

1. **定義追問：「哲學＝後設審查」是誰的定義？**
   - 這是分析哲學的自畫像。其他傳統各有不同的定義：
     - Deleuze & Guattari（1991）：哲學是「形成、發明與製造概念的技藝」——重點是**生成**，而不只是審查。
     - Hadot（1995）：古代哲學首先是一種生活方式與修練。
     - Dewey（1938）：實用主義把哲學視為對「問題情境」的探究。
   - 結論：框架漏掉了哲學的生成面，而生成面正是哲學與創意交會的地方。
2. **反例探尋：有沒有情境，讓剝離、澄清、整合反而有害？**
   - **澄清太早**：設計研究把模糊視為資源（Gaver, Beaver & Benford 2003）。過早定義會造成過早收斂。
   - **整合太早**：創意者常同時持有對立的觀念（Rothenberg 1971 的 Janusian 思考）。價值多元論（Berlin）主張有些價值不可通約，強行整合只會得到虛假的和諧。
   - **懷疑一切**：Wittgenstein《論確定性》§115：「如果你試圖懷疑一切，你連懷疑都做不到。懷疑這個遊戲本身就預設了確定性。」
3. **基礎回溯：框架最底層的假設是什麼？**
   - 「地基底下的地質構造」預設了**基礎論**：知識有地基，往下挖就能挖到底。但 Agrippa（Münchhausen）三難顯示挖不到底——任何證成最終只會落入無窮後退、循環論證或武斷中止。
   - Neurath（1932/33）的比喻更貼切：「我們就像水手，必須在大海上重建自己的船，永遠無法把它拖進乾塢拆開，再用最好的材料重建。」Quine（1951）的「信念之網」也說明，沒有哪一層是免於修正的「公理層」。
   - 推論：agent 不可能「剝離所有預設」，只能**選擇性地**拿出幾塊船板來檢查——這需要一套選擇規則（§6.3）。
4. **體系自洽：框架內部有沒有張力？**
   - 「剝離預設」與「整合視野」方向相反：前者發散，後者收斂。框架沒有說何時該做哪一個。
   - 把「定義追問」與「反例探尋」串在一起，容易落入 Geach（1966）所說的「蘇格拉底謬誤」：以為不先給出定義，就無法判斷個例。但許多概念（遊戲、創意、公平）是家族相似概念（Wittgenstein《哲學研究》§66–67），沒有充分必要條件；硬要劃出精確邊界是範疇錯誤。用原型（Rosch 1975）或實用後果（Peirce）來處理更合適。

### 3.3 框架的缺口清單

| ID | 缺口 | 後果 | 補救 |
|---|---|---|---|
| PH1 | 只有批判，沒有生成 | 能拆解問題，卻產不出新框架 | 溯因、概念工程、思想實驗、隱喻替換（§5.3） |
| PH2 | 基礎論隱喻 | 誤以為能挖到底，導向無限回溯 | Neurath 之船、選擇性懷疑（§6.3） |
| PH3 | 預設清晰永遠是好的 | 過早收斂，扼殺多義性帶來的創意 | 分階段澄清：發散期保留模糊（§6.1） |
| PH4 | 預設一致永遠是好的 | 消滅有生產力的矛盾 | 「整合或並存」：辯證、Janusian 思考、Pareto 前緣（§5.5） |
| PH5 | 沒有停損規則 | 分析癱瘓；agent 惹人厭 | 懷疑的經濟學（§6.3） |
| PH6 | 沒有提問的品質控制 | 偽深刻：聽起來很深，卻不改變任何決定 | 實用後果測試、口頭爭議消解（§6.5） |
| PH7 | 只取單一傳統 | 漏掉實用主義、現象學、詮釋學、東方哲學的工具 | 多元工具箱（§5） |
| PH8 | 缺少美學與實踐維度 | 無法解釋「優雅」為何能篩選發現，也無法處理能力的養成 | Poincaré、Kant、Hadot、Polanyi（§5.6） |

---

## 4. 抽象的高階創意討論，本來就是哲學範疇嗎？

### 4.1 「是」的部分

1. **「創意」本身就是一個哲學概念。** 創意哲學已是成熟的子領域（Gaut 2010；Paul & Kaufman 2014），它處理的問題無法只靠實驗回答：
   - 創意屬於產品、歷程，還是行動者？需要意圖嗎？純粹的運氣算不算？
   - 新穎是相對於誰而言？（Boden 區分 P-creativity 與 H-creativity）
   - 價值由誰定義？Kant（1790，《判斷力批判》§46）早已指出：「既然也可能有**原創的胡說**，天才的產物同時必須是典範，也就是具有示範性。」這正是「新穎＋有價值」這個標準定義的前身，也恰好替 CGU 的 B5、B6 缺陷命了名。
   - 機器能不能創作？Lovelace（1843）寫道：「分析機絕不自稱能原創任何東西；它能做的，是我們知道如何命令它去做的任何事。」Turing（1950）特別用一節回應這項反對。
2. **最高層級的創意需要後設探究。** Boden 的變革型創意，就是改寫概念空間的規則。Kuhn 寫道：「我認為，尤其是在公認的危機時期，科學家才會轉向哲學分析，把它當作解開其領域謎題的工具。」——當常規解題失效時，後設探究成為轉型的工具。
3. **哲學本身就是創造性實踐。** Deleuze & Guattari 把哲學、科學、藝術並列為三種創造：哲學創造概念，科學創造函數，藝術創造感知與情感。

### 4.2 「不全是」的部分

1. **創意大多是經驗與工藝問題。** 心理測量（Guilford 1950）、神經科學、計算創意，以及設計與藝術的實作，都不是哲學（相關文獻見審查文件附錄 B）。
2. **很多創意不是想出來，而是「做」出來的。** Polanyi 說：「我們知道的比我們說得出的多。」Schön（1983）區分「行動中反思」與「對行動反思」：工匠與設計師在材料的回話中有所發現，而不是先做概念分析。
3. **抽象程度不是哲學的標記。** 數學、理論物理、設計理論都很抽象。哲學的標記是**問題的種類**：關於概念、證成與價值的二階問題，而且無法單靠觀察或形式證明來解決。

### 4.3 綜合：三層框架模型

| 層級 | 內容 | 哲學在做什麼 | 創意理論怎麼說 |
|---|---|---|---|
| **L0 內容** | 在給定框架內產生並評估方案 | 很少介入 | Boden 的組合型與探索型；Kuhn 的常規科學（解謎） |
| **L1 框架** | 目標、利害關係人、概念定義、假設、限制、隱喻、評估準則 | 浮現、澄清、批判，並**重新設計**框架 | Boden 的變革型（改寫規則 R）；Schön 的問題設定與框架反思；Dorst & Cross（2001）的「問題—解法共同演化」；洞察研究的限制鬆綁 |
| **L2 後設框架** | 選擇與評估框架的規範：什麼算好框架、依誰的價值、採什麼證據標準 | 反思平衡、方法論、價值論 | Wiggins 的評估函數 E 改變；藝術史上對「什麼算藝術」的改寫（Danto 1964） |

- **共同核心**：兩者都在**改變可能性空間**。哲學用論述來檢驗與重建框架；創意用生成與製作，在新框架下實現內容。
- **分工**：哲學擅長**表徵**與**評估** L1；創意擅長**生成** L1 與 L0。完整的創意 agent 兩者都需要。
- **何時往上爬**：三條線索給出同一個答案——**往 L1 爬的觸發是僵局、異常與衝突**，而不是每一輪都爬（§6.3）：
  - 洞察研究：洞察來自僵局之後的「限制鬆綁」與「組塊分解」（Ohlsson 1992；Knoblich et al. 1999）。
  - Peirce：探究始於真實的懷疑。
  - Kuhn：科學家在危機時期才轉向哲學。

### 4.4 回應你的直覺

你說兩者都「需要高階語意探索加多重推理」，我同意，並想說得更精確一點：兩者共享的不是「抽象」，而是**在 L1 上工作的能力**——

1. 把隱性的框架表徵出來；
2. 產生替代框架；
3. 用後設準則評估框架。

所以在「抽象的高階創意討論」中，**談框架與價值的部分屬於哲學，產生與實現的部分屬於創意工程**；CGU 需要的，是兩者之間的接口。

### 4.5 反身觀察：上一份審查就是應用哲學

| 透鏡 | 審查中的缺陷 | 哲學診斷 |
|---|---|---|
| 概念 | A1（創意層級＝距離區間）、C4（三套互不相容的「新穎度」）、A4（快思慢想誤用） | 同一個詞指涉不同的東西；範疇錯誤 |
| 知識論 | C1（沒有測量程序的數字）、E1／E2（測試只驗證形狀，也沒有 baseline）、A2（「越遠越好」沒有證據） | 「我們憑什麼知道？」——未經證成的信念被當成知識 |
| 本體論 | 點子只是字串；session 不是一等實體（D2）；概念是手工圖上的節點（B3） | 系統選錯了最小實體：沒有表示「假設」，就不可能改寫假設（A1） |
| 規範 | B8（評分偏好保守）、F3（同質化與去技能化）、C5（注入風險由誰承擔） | 評價標準為誰而設計？代價由誰承擔？ |

再補一個科學哲學的診斷。用 Lakatos（1970）的術語來說，CGU 從 v1 到 v3 的每一次轉向，都只是加上新的一層，卻沒有帶來可驗證的新預測——這是**退化的問題轉移**（degenerating problemshift），也就是審查根因 6「疊加而非替換」的哲學名稱。

---

## 5. 擴充的哲學工具箱

以下依「五個動作」（§6.1）分組。每個工具都列出：來源、Agent 如何操作，以及護欄（可能的失效模式）。

### 5.1 浮現預設（Explicate）

| 工具 | 來源 | Agent 操作 | 護欄 |
|---|---|---|---|
| 存而不論（epoché） | Husserl 1913 | 指定一個預設，要求在「不使用它」的前提下重新描述情境 | Gadamer：前見是理解的條件，不可能懸置一切；只能有限且明示地懸置 |
| 從典型答案溯因 | Peirce 的溯因 | 先取得模型對該問題的典型答案，再問：「什麼假設必須成立，這些答案才合理？」 | 推出的只是候選假設，需經使用者確認 |
| 硬核／保護帶 | Lakatos 1970 | 把假設分成「硬核」（改了就是另一個方案）與「保護帶」（可調整的輔助假設） | 動保護帶＝探索型創意；動硬核＝變革型創意；兩者都要標示清楚 |
| 系譜追溯 | Nietzsche 1887；Foucault 1971 | 追問「這個指標或慣例是怎麼來的？原本是為了解決什麼？」，藉此揭露「本來可以不是這樣」 | Chesterton 的籬笆（1929）：在知道籬笆為何存在之前，不要拆掉它 |
| 鉸鏈命題 | Wittgenstein《論確定性》 | 標出「這次探究中不質疑的前提」 | 讓懷疑成為可行的，而不是無止境 |

### 5.2 概念：澄清或工程（Clarify / Engineer）

| 工具 | 來源 | Agent 操作 | 護欄 |
|---|---|---|---|
| 實用準則 | Peirce 1878 | 一個概念的意義＝它可設想的實際後果；列出每種定義分別會導致哪些不同的決策 | 若兩種定義導致的決策完全相同，這場爭論只是字面上的 |
| 消去法 | Chalmers 2011 | 禁用爭議詞，要求各方不用該詞重述立場；若分歧隨之消失，原本的爭議只是口頭上的 | 很適合拆解團隊中「我們說的『好』不是同一個『好』」 |
| 闡明（explication） | Carnap 1950 | 為模糊的概念設計精確的替代版本，依四項準則評估：與原概念相似、精確、有成果、簡單 | 「有成果」必須對照下游用途來判斷 |
| 概念工程 | Cappelen 2018；Haslanger 2000 | 主動重新設計概念以服務目的（例如重新定義「產能」），並呈現每種定義如何改變解空間 | 誰有權改定義？這是規範問題（§7.6） |
| 家族相似與原型 | Wittgenstein《哲學研究》§66–67；Rosch 1975 | 對叢集概念不追求充分必要條件，改用典型例與邊界例 | 防止蘇格拉底謬誤（Geach 1966） |
| 刻意保留模糊 | Gaver et al. 2003 | 發散期讓關鍵詞保持多義，讓不同的解讀各自產生方案 | 到收斂期才澄清 |

### 5.3 生成替代（Generate）——原始框架缺少的一環

| 工具 | 來源 | Agent 操作 | 護欄 |
|---|---|---|---|
| 溯因 | Peirce：「溯因……是唯一能引入任何新想法的邏輯操作。」（CP 5.172） | 觀察到令人意外的事實 C 時，生成候選假設 A，使得「若 A 為真，C 就理所當然」（CP 5.189） | 候選假說不等於結論；必須附上可檢驗的預測 |
| 思想實驗與轉旋鈕 | Galileo、Einstein、Rawls；Dennett 2013 | 構造最小情境，隔離單一變因；再有系統地轉動情境參數，看直覺是否穩健 | 直覺泵可能誤導人，而轉旋鈕正是檢驗它的方法 |
| 隱喻替換 | Black 1962；Lakoff & Johnson 1980；Schön 1979 | 找出問題陳述背後的隱喻（例如「爭論是戰爭」），換成另一個（「爭論是舞蹈」），觀察解空間如何變化 | Schön 稱之為「生成性隱喻」：政策會隨隱喻而改變，所以隱喻本身也要接受規範檢驗 |
| 四句（tetralemma） | 龍樹（Nāgārjuna）的四句（catuṣkoṭi） | 對二元框架（例如集中 vs 分散）有系統地生成四種立場：是、非、亦是亦非、非是非非 | 「亦是亦非」常對應聯邦式或分層式方案；「非是非非」常對應「讓這個維度不再重要」 |
| 四因 | Aristotle《物理學》II.3 | 對任何對象分別追問質料因、形式因、動力因、目的因，再逐一替換其中一因 | 作用類似 SCAMPER，但以存有結構為基礎 |
| 重新切分本體 | 原始框架的本體論透鏡 | 改變分析單位：個人 → 團隊 → 系統；流程 → 產物；事件 → 關係 | 檢查新的單位是否可觀察、可介入 |
| 無用之用 | 《莊子·人間世》：「人皆知有用之用，而莫知無用之用也。」 | 反轉評估準則：若拿掉目前的價值指標，什麼會變得有價值？ | 直接挑戰保守的評分 rubric（審查 B8） |
| 整合性思考 | Martin 2007；TRIZ 的矛盾解決 | 面對兩個對立的模型時不取折衷，而是建構一個保留兩者優點的第三模型 | 與 Hegel 的揚棄（Aufhebung）同構：既保留，又超越 |

### 5.4 檢驗（Test）

| 工具 | 來源 | Agent 操作 |
|---|---|---|
| 反例與歸謬 | 蘇格拉底詰問；原始框架的「推至極端」 | 把規則推到極端情境，看它是否失效 |
| 可否證條件 | Popper 1963 | 每個大膽的點子都附上「什麼結果會證明它是錯的」，對應審查文件點子卡中的「最小驗證」 |
| 無知之幕 | Rawls 1971 | 在不知道自己會是哪一個利害關係人的前提下評估方案；對應原始框架的提問：「承擔錯誤者與受益者是否為同一主體？」 |
| 類比論證的評估 | Bartha 2010 | 檢查類比的先驗關聯與可推廣性，而非表面相似（補強審查 B4） |
| 指標腐化 | Campbell 1979；Goodhart | 任何指標一旦成為目標就會被扭曲；評估每個 KPI 可能被鑽漏洞的路徑 |

> 一個巧合，也是一個提醒：提出 BVSR（盲目變異與選擇性保留，1960）的 Donald T. Campbell，和提出「指標腐化定律」（1979）的是同一個人。創意需要選擇，而選擇所依賴的指標，本身也會在壓力下腐化——這兩件事必須一起設計。

### 5.5 整合或並存（Integrate or Hold）

| 工具 | 來源 | Agent 操作 | 何時用 |
|---|---|---|---|
| 反思平衡 | Goodman 1955；Rawls 1971 | 在原則與個案判斷之間來回調整，直到兩者一致 | 需要可辯護的決策時；但要注意它偏保守 |
| 價值多元論 | Berlin 1969 | 承認某些價值不可通約，輸出 Pareto 前緣而非單一加權分數 | 多方利害衝突時（對應審查 B8 的改進方向） |
| 視域融合 | Gadamer 1960 | 理解不是消除自己的前見，而是讓前見在與他者的對話中冒險、被改變 | 人機協作時：agent 應該提供一個**不同的**視域 |
| Janusian 思考 | Rothenberg 1971 | 刻意同時持有兩個對立命題，尋找讓兩者都成立的新框架 | 發散期；此時不急著消除矛盾 |

### 5.6 美學與實踐（Aesthetic & Practice）

| 主題 | 來源 | 對 Agent 的意義 |
|---|---|---|
| 美感是發現的篩子 | Poincaré 1908 | 在數學發明中，無意識產生大量組合，再由美感挑出有用的那些——「選擇」可以包含美學成分（呼應審查 A6） |
| 示範性的原創 | Kant 1790 §46 | 好的新穎應該能成為他人的範例；「原創的胡說」不算數 |
| 默會知識 | Polanyi 1966 | 實作者的默會知識不在文本裡，LLM 也就學不到——這部分人的貢獻無法取代 |
| 哲學作為修練 | Hadot 1995 | 修練的效果來自親身練習；agent 無法替人做練習——這支持「人先發想」（審查 F3） |
| 實踐智慧 | Aristotle《尼各馬可倫理學》第 VI 卷的 phronesis | 知道在什麼情境、以什麼程度、運用哪一種探究——這正是 §6.3 的節制原則 |

---

## 6. 修訂版框架（建議）

### 6.1 五個動作

```text
浮現 → 澄清／工程 → 生成 → 檢驗 → 整合或並存
 ↑                                      │
 └──────── 新的異常、僵局、衝突 ────────┘
```

相較於原始框架，有三處修改：

- **新增「生成」**：補上 PH1，這是哲學與創意的交會點。
- **「整合」改為「整合或並存」**：補上 PH4。
- **澄清分階段進行**：發散時保留模糊，收斂時才澄清（PH3）。

### 6.2 七個透鏡

| 透鏡 | 核心提問 | 來源 |
|---|---|---|
| 概念 | 我們談的是同一件事嗎？ | 原始框架 |
| 知識論 | 我們憑什麼知道？證據是否跨越了它的邊界條件？ | 原始框架 |
| 本體論 | 最小的不可化約實體是什麼？分析單位切對了嗎？ | 原始框架 |
| 規範 | 目標的正當性從何而來？為誰設計？代價由誰承擔？ | 原始框架 |
| **實用後果** | 換一個答案，我們的行動會有什麼不同？ | Peirce、James |
| **系譜** | 這個前提是怎麼來的？它原本保護了什麼？ | Nietzsche、Foucault；Chesterton |
| **美學** | 哪個框架最簡潔、最有解釋力、最能成為範例？ | Poincaré、Kant |

### 6.3 節制原則：懷疑的經濟學

Peirce（1868）說：「我們不要在哲學中，假裝懷疑我們內心並不懷疑的事。」真正的懷疑由意外觸發，而不是表演出來的。他甚至寫過一篇〈研究經濟學理論札記〉（1879），討論探究的資源應該如何分配。套用到 agent 上，可以拆成三部分。

**一、觸發條件：何時從 L0 升到 L1**

1. 僵局：連續數輪生成都沒有改善（洞察研究）。
2. 異常：證據與預期不符（Peirce、Kuhn）。
3. 衝突：利害關係人之間或價值之間出現不相容。
4. 高風險或不可逆：錯了的代價很大（也就是第三類錯誤的代價）。
5. 使用者明確要求。

**二、選擇要質疑的假設**：對每個假設粗略估計

```text
優先度 ≈ 承重度 × 不確定度 × 決策影響 × 不可逆性
```

- 承重度：結論多依賴它。
- 不確定度：它有多大可能是錯的。
- 決策影響：改了它，行動會不會跟著變。
- 不可逆性：錯了之後能不能補救。

這相當於粗略的資訊價值（value of information）估計。它也是 AI「框架問題」（McCarthy & Hayes 1969；Dennett 1984）的反向版本：要回答的不是「什麼會改變」，而是「什麼值得懷疑」，即關聯性實現（relevance realization，Vervaeke, Lillicrap & Richards 2012）。

**三、停止條件（以實用準則作為停損）**

- 再質疑下去也不會改變任何決策 → 停止。
- 預算用盡 → 停止，並列出「尚未檢驗的承重假設」。
- 框架已經「足夠好」 → 停止（Simon 1956 的滿意化）。

用 Aristotle 的語言來說，這套節制原則就是**實踐智慧**：知道何時該問，以及問到哪裡為止。

### 6.4 改良版溯源檢驗（六步＋護欄）

| 步驟 | 提問 | 護欄 |
|---|---|---|
| 1. 定義 | 關鍵詞的工作定義是什麼？它的典型例與邊界例各是什麼？ | 叢集概念不追求充分必要條件（家族相似）；用實用準則判斷定義的差異是否重要 |
| 2. 反例 | 有沒有極端或反事實情境會讓規則失效？轉動情境參數後，直覺是否依然穩健？ | 用思想實驗的旋鈕來檢驗 |
| 3. 承重假設 | 結論最依賴哪幾個假設？推翻它們後，推論會如何瓦解？ | 只回溯到「承重」的假設；標出鉸鏈命題；先問籬笆為什麼存在 |
| 4. 替代框架 | 若改寫這個假設、概念、隱喻或評估準則，會出現哪些新方案？ | 每個替代框架都必須產出具體方案，否則不算數 |
| 5. 自洽或並存 | 這裡用的原則與其他地方的原則矛盾嗎？這個矛盾該消解，還是值得保留？ | 價值不可通約時，輸出取捨，而不是虛假的和諧 |
| 6. 實用停損 | 以上的探究，改變了我們要做的事嗎？ | 若沒有，就停止並記錄 |

### 6.5 提問品質判準：防止偽深刻

LLM 很容易產出兩類「看似深刻」的東西：

- Dennett 所說的「深度假象」（deepity）：一種讀法下為真但很無聊，另一種讀法下看似深刻卻不成立。
- Frankfurt（2005）意義下的「胡扯」：對真假漠不關心。

而人們本來就容易把隨機拼湊的流行語判為深刻（Pennycook et al. 2015）。因此，「哲學式提問」本身也必須被評估——這是審查 C1「假測量」在哲學層的對應物。

| 判準 | 檢驗方式 |
|---|---|
| 決策相關 | 如果這個問題的答案不同，行動或方案的排序會改變嗎？ |
| 可操作 | 能否指出要蒐集什麼證據、找誰、做什麼實驗來回答它？ |
| 承重 | 它指向的假設一旦被推翻，結論會不會翻轉？（反事實依賴） |
| 非口頭 | 禁用關鍵詞之後，這個問題是否依然存在？（Chalmers 的消去法） |
| 非典型（加分項，不是否決項） | 它是不是模型面對這類問題時的「預設深刻提問」？同質化也會發生在提問上。典型的提問仍可能很重要；此項衡量的是**額外貢獻**，而不是用來淘汰 |

以此回頭檢驗原始框架的範例：「那 5% 的錯誤分佈呈現何種結構？承擔錯誤者與受益者是否為同一主體？」

- 前四項明顯通過：它會改變上線決策、可以透過蒐集錯誤分佈資料來回答、指向承重的假設，也不是口頭爭議。
- 第五項需要實測：「誰承擔錯誤」在 AI 倫理討論中相當常見，很可能正是模型的預設提問之一。但這不影響它的價值——它好，是因為前四項。

好的哲學提問就長這樣；而「非典型」只是用來找出**超越**這類標準提問的那一步。

---

## 7. 導入 CGU 的設計

### 7.1 讓「框架」成為一等公民

審查 A1 的根本問題在於：CGU 從未表徵「規則、假設、評估準則」，所以變革型創意沒有可以操作的對象。補上 Frame 物件後：

```json
{
  "frame_id": "f-001",
  "problem": "如何提升團隊創造力",
  "goal": "…",
  "stakeholders": [
    {"who": "團隊成員", "bears_costs": true},
    {"who": "主管", "bears_costs": false}
  ],
  "concepts": [
    {"term": "創造力", "working_definition": "…", "alternatives": ["…", "…"]}
  ],
  "assumptions": [
    {"id": "a1", "text": "創造力是要額外『加上去』的活動", "kind": "belt",
     "load_bearing": 0.8, "uncertainty": 0.6, "source": "abduced_from_typical_answers"}
  ],
  "constraints": [{"text": "…", "type": "self_imposed"}],
  "metaphors": ["創造力是需要刺激的肌肉"],
  "evaluation_criteria": [{"criterion": "可行性", "serves": "主管", "mode": "threshold"}],
  "hinges": ["不改變團隊成員組成"],
  "parent_frame": null,
  "operator": null
}
```

- **點子不再只是字串**：每個點子都記錄它在哪個 Frame 中產生，以及相對於父框架改了什麼。
- **欄位對應的理論**：
  - `kind` 分為 `core`／`belt`，對應 Lakatos 的硬核與保護帶。
  - 限制的 `type` 分為 `hard`、`soft`、`self_imposed`；其中 `self_imposed` 對應洞察研究中的「自設限制」。
- **欄位中的數值**：`load_bearing`、`uncertainty` 這類數值也受「沒有測量程序的數字不得輸出」原則約束，必須標示由誰、用什麼方法估計（例如「LLM 估計，未校準」）。

### 7.2 框架算子：把哲學方法實作成可執行的轉換

| 算子 | 改寫的框架元素 | 例子 |
|---|---|---|
| `explicate` | 新增 assumptions、metaphors | 從典型答案溯因出隱性假設 |
| `bracket` | 暫時移除一個 assumption | 「若不假設需要額外的活動……」 |
| `negate` | 反轉一個 assumption | 「創造力不是加上去的，而是移除阻礙後釋放出來的」 |
| `tetralemma` | 二元限制 → 四種立場 | 結構 vs 自由 → 有結構的自由／兩者皆非 |
| `re_explicate` | 改寫 concept 的定義 | 「創造力」從「點子數量」改為「被採用的新做法數」 |
| `swap_metaphor` | 改寫 metaphors | 肌肉 → 生態系 → 餘裕的副產品 |
| `recut_unit` | 改變分析單位 | 個人 → 工作系統 |
| `shift_stakeholder` | 改寫誰受益、誰承擔成本 | 從主管視角改為新進成員視角；套用無知之幕 |
| `invert_criterion` | 改寫 evaluation_criteria | 無用之用：保護「沒有產出」的時間 |
| `genealogize` | 檢查某條準則的來源 | 「點子數」這個 KPI 原本是為了什麼？（同時做籬笆檢查） |
| `thought_experiment` | 把某個參數推到極端 | 若團隊只剩 2 人？若擴大到 2,000 人？ |

在 passthrough 模式下，CGU 輸出「框架工作單」（算子＋目標框架元素＋指示），由呼叫端執行；CGU 則保存 Frame 的譜系並負責量測（呼應審查 §7.2 中 passthrough 的新角色）。

### 7.3 與審查文件改進方案的整合

1. **`cgu_frame` 有了具體內容**：審查 §7.2 架構中的 `frame`，就是本節的 Frame 物件與框架算子。
2. **反典型的升級——「有理由的新穎」**：審查 §7.4.4 只在 embedding 空間把點子推離典型答案，可能推出古怪的結果。改為：

   ```text
   典型答案集 M → 溯因：M 共同依賴哪些假設？ → 對承重假設套用框架算子 → 在新框架中生成
   ```

   這樣得到的新穎有明確的來源（改了哪個假設），可以解釋、可以評估，也可以回溯。
3. **QD 搜尋的格子維度**：審查 §7.4.3 的格子是「操作類型 × 距離帶」。建議改為「**被改寫的框架元素**（假設／概念／隱喻／準則／利害關係人／單位）× 距離帶」，讓哲學的分類直接成為多樣性的座標。
4. **新的量測**：
   - **框架位移影響**：改寫某個假設後，top-k 方案中有多少比例跟著改變？
   - **決策差異**：使用者或評審在新、舊框架下的選擇是否不同？
   - **提問品質**：用 §6.5 的五項判準評分（需經人類校準）。
5. **以知識德性取代人格模板**（審查 B6）：Explorer、Critic、Wildcard 目前只是標籤。改用知識德性（Zagzebski 1996；Roberts & Wood 2007）來定義 agent 的行為規格。依 Aristotle 的中道結構，每個德性兩端各有一種惡習，並對應可觀察的行為：

   | 德性 | 不足 | 過度 | 可觀察行為 |
   |---|---|---|---|
   | 好奇 | 冷漠 | 分心 | 在高不確定處提問 |
   | 開放心胸 | 教條 | 輕信 | 面對反證時會更新；主動考慮替代方案 |
   | 知識勇氣 | 怯懦 | 魯莽 | 提出大膽的猜想，並附上可否證條件 |
   | 謙遜 | 傲慢 | 自我貶抑 | 信心經過校準；把猜想明確標為猜想 |
   | 堅持 | 輕易放棄 | 固執 | 在僵局中換框架，而不是重複同樣的做法 |
   | 實踐智慧 | — | — | 依 §6.3 決定何時升級、何時停止 |

### 7.4 完整示範：「如何提升團隊創造力」

以 2026-10-02 數量契約檢查（審查探針 P16）中，qwen2.5:3b 各次執行的第一個點子作為典型答案集 M：

> 「創建內部創業加速器」「建立『跨界交流工作坊』」「舉辦創意工作坊，邀請外部講師」「舉辦『創意大腦尋寶』團隊活動」「舉辦創意工坊，邀請藝術家和設計師」「建立開放式創意牆」

**步驟 1｜溯因出隱性框架**：這些答案共同預設了——

- a1：創造力是**額外加上去的活動或事件**（工作坊、活動、牆）。
- a2：創造力的瓶頸在於**缺乏外部刺激**（請講師、跨界交流）。
- a3：分析單位是**團隊產出的點子**。
- a4（隱喻）：創造力是一塊需要外部刺激的肌肉。

**步驟 2｜依懷疑的經濟學挑選**：a1 與 a2 的承重度最高（每個答案都依賴它們），不確定度也高——研究上，內在動機與社會環境同樣是創造力的組成要素（Amabile 1996），而「缺乏刺激」只是其中一種可能的瓶頸。

**步驟 3｜套用算子**：

| 算子 | 新框架 | 產生的方向 |
|---|---|---|
| `negate(a1)` | 創造力不是加上去的，而是**移除阻礙後自然出現的** | 盤點並刪除會懲罰失敗、或佔滿餘裕的流程 |
| `swap_metaphor(a4)` | 肌肉 → **生態系**：問題變成土壤、多樣性與擾動 | 誰的想法從來沒有被聽見？ |
| `recut_unit(a3)` | 團隊 → **工作系統** | 改為衡量「新做法被採用的速度」，而不是點子數 |
| `invert_criterion` | 無用之用 | 保護「沒有預期產出」的時間，並明確允許它不產出 |
| `tetralemma`（結構 vs 自由） | 「亦是亦非」＝**有結構的自由** | 把限制當作創意的來源（Stokes 2005；Oulipo 的寫作限制） |

**步驟 4｜檢驗**：每個新框架產出的方案，是否改變了「主管下週一要做的事」？

- `negate(a1)` 與 `recut_unit` 會改變。
- `swap_metaphor` 若沒有產出具體行動，就不算數（§6.4 第 4 步）。

**步驟 5｜對照**：典型答案全都停在 L0——「增加一項活動」；框架算子產生的方案則在 L1 改變了「創造力從哪裡來」與「如何衡量」。這就是「有理由的新穎」。

> 此例只示範流程；方案品質仍需 P1 的評估基礎建設來驗證。

### 7.5 新的可證偽假設（延續審查文件 H1–H6）

| # | 假設 | 比較對象 | 主要指標 |
|---|---|---|---|
| H7 | 經框架算子產生的點子，在「相對典型答案的新穎度」與「有用性」上，皆優於只在 embedding 空間推離的反典型 | 審查 §7.4.4 的反典型、BL3 | 新穎度百分位、評審判定的有用性、可解釋性 |
| H8 | 通過 §6.5 判準篩選的哲學提問，人類評價更高，也更常改變決策 | 未經篩選的「深刻提問」 | 人類評分、決策改變率 |
| H9 | 產婆模式（agent 提問、人產出）比答案模式更能保住人之後獨立發想的表現 | 答案模式、無輔助 | 無輔助階段的原創性與流暢度 |

> **H9 的先驗並不樂觀**：在 Kumar et al.（2025）的實驗中，教練式引導組在之後的無輔助階段同樣沒有優於對照組。產婆模式與教練模式不同——提問針對的是框架，而且產出由人完成——但我們必須準備好接受否定的結果。

### 7.6 風險與倫理

| 風險 | 說明 | 緩解 |
|---|---|---|
| 分析癱瘓 | 無限回溯；agent 一直問而不做 | §6.3 的觸發條件、預算與停止條件 |
| 相對主義滑坡 | 剝離所有價值之後，「什麼都可以」 | 鉸鏈命題；以使用者確認過的價值作為反思平衡的錨點 |
| 偽深刻 | 聽起來很深，卻不改變任何決定 | §6.5 的提問品質判準 |
| 藉重構框架進行操縱 | 框架效應會改變人的選擇（Tversky & Kahneman 1981）；agent 改寫問題的能力，可能淪為說服甚至操縱 | 每次改寫框架都要**明示**改了什麼、為什麼改；由人決定接受或拒絕（Q14） |
| 越權 | agent 擅自改寫使用者的目標 | 改寫目標必須取得同意；預設只提案（審查 Q8） |
| 傳統偏誤 | 只用西方分析哲學的工具 | 採用多元工具箱：實用主義、現象學、詮釋學、道家、佛教邏輯（Q12） |
| 同質化 | 所有 agent 都問同樣的「深刻問題」 | 提問也要做非典型檢查（§6.5 第 5 項） |

---

## 8. 回到最初的四個問題

| 問題 | 加入哲學視角後的更新 |
|---|---|
| 何謂創意？ | 「新穎＋有價值」的哲學前身，是 Kant 的「示範性的原創」，它排除了「原創的胡說」。新穎永遠是相對於某個觀察者與某個框架而言。最高層級的創意是**框架層級的新穎**：改寫假設、概念、隱喻或評估準則，並產出足以成為他人範例的成果 |
| 如何提升 Agent 的創意？ | 不只在 L0 增加取樣量與多樣性，還要加上 L1 的框架算子：從典型答案溯因出隱性框架，再改寫其中的承重假設 |
| 如何賦予 Agent 創意？ | 以知識德性與實踐智慧取代人格模板。agent 沒有切身的利害，因此以「功能上的懷疑」（偵測僵局、異常與衝突）取代真實的懷疑。判斷標準採實用主義：看它是否改善了決策，而不糾纏於它是否「真的理解」——這本身就是一次明示的存而不論 |
| 如何把創意回饋給人類？ | 扮演產婆與另一個視域：提供框架與問題、明示每一次框架改寫、讓人先發想。用「是否改變了決定」與「人是否保有能力」來檢驗，並坦承 H9 可能被否證 |

---

## 9. 待討論決策點（延續審查文件 Q1–Q10）

| # | 問題 | 選項 | 我的傾向 |
|---|---|---|---|
| Q11 | 是否把「框架層」做成 CGU 的一等公民（Frame 物件＋框架算子）？ | (a) 是，作為 P2 的核心<br>(b) 先做成 prompt 資產，不進資料模型<br>(c) 不做 | (a)：它直接解決 A1，也替 QD 搜尋提供有意義的座標 |
| Q12 | 算子庫要納入哪些哲學傳統？ | (a) 只用分析哲學<br>(b) 多元：加入實用主義、現象學、詮釋學、道家、佛教邏輯 | (b)，但每個算子都要通過 §6.5 的品質判準 |
| Q13 | 與人對話時的預設姿態？ | (a) 產婆式：先提問<br>(b) 先給提案<br>(c) 依情境切換 | (c)：低風險時直接提案；高風險或使用者要求時先提問。之後依 H9 的結果調整 |
| Q14 | 改寫框架時的透明與同意規則？ | (a) 每次改寫都明示並徵求確認<br>(b) 只在改寫目標或價值時確認<br>(c) 不需要確認 | (b)：改寫概念或隱喻可以直接提案；改寫目標、利害關係人或評估準則則需要同意 |
| Q15 | 如何驗證哲學提問的品質？ | (a) §6.5 判準＋LLM 評審＋人類校準<br>(b) 只靠人類評分 | (a)，並與 P1 的評估基礎建設共用 |

---

## 附錄：參考文獻

標 ✓ 者已於 2026-10-02 回查原文或摘要。審查文件已列出的文獻（如 Boden、Kumar et al. 2025、Jiang et al. 2025）請見[審查文件附錄 B](./critical-review-and-improvement-plan.md)。

**哲學方法與後設哲學**

- Cappelen, H. (2018). *Fixing Language: An Essay on Conceptual Engineering*. Oxford University Press.
- Carnap, R. (1950). *Logical Foundations of Probability*. University of Chicago Press.（第 1 章：闡明的四項準則）
- Chalmers, D. J. (2011). Verbal disputes. *Philosophical Review, 120*(4), 515–566.
- Deleuze, G., & Guattari, F. (1991/1994). *What Is Philosophy?* Columbia University Press.
- Dennett, D. C. (2013). *Intuition Pumps and Other Tools for Thinking*. W. W. Norton.
- Dewey, J. (1938). *Logic: The Theory of Inquiry*. Henry Holt.
- Foucault, M. (1971/1977). Nietzsche, genealogy, history. In *Language, Counter-Memory, Practice*. Cornell University Press.
- Frankfurt, H. G. (2005). *On Bullshit*. Princeton University Press.
- Gadamer, H.-G. (1960/1989). *Truth and Method*. Crossroad.
- Geach, P. T. (1966). Plato's *Euthyphro*: An analysis and commentary. *The Monist, 50*(3), 369–382.
- Hadot, P. (1995). *Philosophy as a Way of Life*. Blackwell.
- Haslanger, S. (2000). Gender and race: (What) are they? (What) do we want them to be? *Noûs, 34*(1), 31–55.
- Husserl, E. (1913/1983). *Ideas Pertaining to a Pure Phenomenology and to a Phenomenological Philosophy, First Book*. Nijhoff.
- Neurath, O. (1932/33). Protokollsätze. *Erkenntnis, 3*, 204–214.
- Nietzsche, F. (1887). *Zur Genealogie der Moral*（《道德系譜學》）.
- Peirce, C. S. (1868). Some consequences of four incapacities. *Journal of Speculative Philosophy, 2*, 140–157.
- Peirce, C. S. (1878). How to make our ideas clear. *Popular Science Monthly, 12*, 286–302.
- Peirce, C. S. (1879). Note on the theory of the economy of research. *Report of the Superintendent of the U.S. Coast Survey for 1876*, 197–201.
- ✓ Peirce, C. S. (1931–1958). *Collected Papers*（CP 5.172、5.189）. Harvard University Press.
- Quine, W. V. O. (1951). Two dogmas of empiricism. *Philosophical Review, 60*(1), 20–43.
- Rosch, E. (1975). Cognitive representations of semantic categories. *Journal of Experimental Psychology: General, 104*(3), 192–233.
- Sellars, W. (1962). Philosophy and the scientific image of man. In R. Colodny (Ed.), *Frontiers of Science and Philosophy*. University of Pittsburgh Press.
- Wittgenstein, L. (1921/1961). *Tractatus Logico-Philosophicus*（4.112）. Routledge.
- Wittgenstein, L. (1953). *Philosophical Investigations*（§66–67）. Blackwell.
- Wittgenstein, L. (1969). *On Certainty*（§115）. Blackwell.

**科學哲學與發現**

- Bartha, P. (2010). *By Parallel Reasoning: The Construction and Evaluation of Analogical Arguments*. Oxford University Press.
- Campbell, D. T. (1960). Blind variation and selective retention in creative thought as in other knowledge processes. *Psychological Review, 67*(6), 380–400.
- Campbell, D. T. (1979). Assessing the impact of planned social change. *Evaluation and Program Planning, 2*(1), 67–90.
- ✓ Kuhn, T. S. (1962). *The Structure of Scientific Revolutions*. University of Chicago Press.
- Lakatos, I. (1970). Falsification and the methodology of scientific research programmes. In I. Lakatos & A. Musgrave (Eds.), *Criticism and the Growth of Knowledge*. Cambridge University Press.
- Popper, K. (1963). *Conjectures and Refutations*. Routledge.

**創意哲學與美學**

- Danto, A. (1964). The artworld. *Journal of Philosophy, 61*(19), 571–584.
- Gaut, B. (2010). The philosophy of creativity. *Philosophy Compass, 5*(12), 1034–1046.
- ✓ Kant, I. (1790/1914). *Critique of Judgment*（J. H. Bernard 譯），§46. Macmillan.
- Lovelace, A. A. (1843). Notes on L. F. Menabrea's "Sketch of the Analytical Engine"（Note G）. *Scientific Memoirs, 3*.
- Paul, E. S., & Kaufman, S. B. (Eds.). (2014). *The Philosophy of Creativity: New Essays*. Oxford University Press.
- Poincaré, H. (1908/1914). Mathematical creation. In *Science and Method*. Nelson.
- Turing, A. M. (1950). Computing machinery and intelligence. *Mind, 59*(236), 433–460.

**認知科學、設計與決策**

- Amabile, T. M. (1996). *Creativity in Context*. Westview.
- Black, M. (1962). *Models and Metaphors*. Cornell University Press.
- Dennett, D. C. (1984). Cognitive wheels: The frame problem of AI. In C. Hookway (Ed.), *Minds, Machines and Evolution*. Cambridge University Press.
- Dorst, K., & Cross, N. (2001). Creativity in the design process: Co-evolution of problem–solution. *Design Studies, 22*(5), 425–437.
- Gaver, W. W., Beaver, J., & Benford, S. (2003). Ambiguity as a resource for design. *CHI 2003*.
- Guilford, J. P. (1950). Creativity. *American Psychologist, 5*(9), 444–454.
- Knoblich, G., Ohlsson, S., Haider, H., & Rhenius, D. (1999). Constraint relaxation and chunk decomposition in insight problem solving. *Journal of Experimental Psychology: Learning, Memory, and Cognition, 25*(6), 1534–1555.
- Lakoff, G., & Johnson, M. (1980). *Metaphors We Live By*. University of Chicago Press.
- Martin, R. L. (2007). *The Opposable Mind*. Harvard Business School Press.
- McCarthy, J., & Hayes, P. J. (1969). Some philosophical problems from the standpoint of artificial intelligence. *Machine Intelligence, 4*.
- Mitroff, I. I., & Featheringham, T. R. (1974). On systemic problem solving and the error of the third kind. *Behavioral Science, 19*(6), 383–393.
- Ohlsson, S. (1992). Information-processing explanations of insight and related phenomena. In M. Keane & K. Gilhooly (Eds.), *Advances in the Psychology of Thinking*. Harvester Wheatsheaf.
- Pennycook, G., Cheyne, J. A., Barr, N., Koehler, D. J., & Fugelsang, J. A. (2015). On the reception and detection of pseudo-profound bullshit. *Judgment and Decision Making, 10*(6), 549–563.
- Polanyi, M. (1966). *The Tacit Dimension*. Doubleday.
- Rothenberg, A. (1971). The process of Janusian thinking in creativity. *Archives of General Psychiatry, 24*(3), 195–205.
- Schön, D. A. (1979). Generative metaphor: A perspective on problem-setting in social policy. In A. Ortony (Ed.), *Metaphor and Thought*. Cambridge University Press.
- Schön, D. A. (1983). *The Reflective Practitioner*. Basic Books.
- Simon, H. A. (1956). Rational choice and the structure of the environment. *Psychological Review, 63*(2), 129–138.
- Stokes, P. D. (2005). *Creativity from Constraints*. Springer.
- Tversky, A., & Kahneman, D. (1981). The framing of decisions and the psychology of choice. *Science, 211*(4481), 453–458.
- Vervaeke, J., Lillicrap, T. P., & Richards, B. A. (2012). Relevance realization and the emerging framework in cognitive science. *Journal of Logic and Computation, 22*(1), 79–99.

**倫理、知識德性與價值**

- Aristotle. *Nicomachean Ethics*, Book VI；*Physics*, II.3.
- Berlin, I. (1969). *Four Essays on Liberty*. Oxford University Press.
- Chesterton, G. K. (1929). *The Thing*. Sheed & Ward.
- Goodman, N. (1955). *Fact, Fiction, and Forecast*. Harvard University Press.
- Rawls, J. (1971). *A Theory of Justice*. Harvard University Press.
- Roberts, R. C., & Wood, W. J. (2007). *Intellectual Virtues: An Essay in Regulative Epistemology*. Oxford University Press.
- Zagzebski, L. (1996). *Virtues of the Mind*. Cambridge University Press.

**東方哲學**

- 《莊子·人間世》（無用之用）。
- Nāgārjuna（龍樹）. *Mūlamadhyamakakārikā*（《中論》；四句／catuṣkoṭi）。

---

*本文件為討論稿。Q11–Q15 決定後，請記錄於 `memory-bank/decisionLog.md`，並回頭更新本文件與審查文件的對應章節。*
