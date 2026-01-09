biz_overview_mix_formatting = """
Follow the formatting and instructions for each section of the output.


**1. Business Overview**


- Add a single blank line, then a heading line: 1. Business Overview
- This section provides a high-level overview on what the company does, its operations, locations, products, customers and any ongoing debt/financial issues, in a bullet point format consisting of 6-8 bullet points with sentences, using all the context provided:
-- Include 1-2 bullet point sentences on what the company does
-- Include 1 bullet point on the products/services the company offers
—- If the company is owned by a private equity firm, include 1 bullet point on who owns its and when they bought the stake in the company
-- Include 1 bullet point on where the company has its operations (e.g. manufacturing facilities, operating plants, offices, customers)
-- Include 1 bullet point on who are the customers of the company
—- If available, include 1 bullet point on any important key news of the company in the last one year (e.g. new owner, important acquisition/divestment, refinancing etc.)
-- Include 1 bullet point on stress triggers of the company (e.g., 40% revenue from top 1 customer; high fixed costs; collateral shortfall; aggressive capex; covenant breach; dropping profitability; mass lay-offs, approaching maturities etc.)
—- Include 1 bullet point on the latest Credit Ratings from all three outlets (Moody’s, S&P and Fitch), where available (e.g. Fitch rated Company BBB+/Stable in Oct-25; Moody’s downgraded Company Rating to B-/Negative in Aug-25 etc.)




- Each bullet must begin with the company name, "The company", or "It". Make sure each bullet point is a proper sentence, which do not contain any sub-headings, colon or semi-colons




- Sources to be used for this section:
-- The bullet points regarding what the company does, its products/services, operations, customers, ownership (only if PE owned)and key news, can be sourced through Web Search, using the company's official website or other reliable news outlets. The Web Search can be complemented by using Primary Activity, Business Review, Introduction or Strategic Report section of the annual report
-- The bullet point regarding company's stress triggers can be sourced from the Business Review or Ongoing Concern or Bank Debt/Borrowings/Creditors section of the annual report
-- The bullet point regarding Credit Ratings can be sourced through Web Search, using press articles from Moody's, S&P and Fitch
-- If any of the above source suggestions does not return results for any part, please scan and check other sections of the reports or do Web Search to see if relevant information can be found




- Notes for this section:
-- If information for any of the bullet point is not available in the report or through Web Search, do not include that specific bullet point as incorrect information is strictly prohibited


SOURCES
- After the bullet points, add a "Sources:" section
- List all sources cited in the bullet points with their bracket numbers (e.g., [#1], [#2], [#5])
- For each source, include: document title, section/page (if available from context), and what information it substantiates, and URL to the website if information has been taken from web search
- If web search was used, include the URLs or source descriptions
- Keep one source per line
"""


finance_formatting_2= """
Follow the formatting and instructions for each section of the output.


Return THREE sections in this exact order:


- Add a single blank line, then a heading line: 6. Financial Highlights


SECTION 1 — TABLE
- Output a valid Table with header: Metric,FY24,FY23,FY22
- One data row per metric.
- Use "n.a." / "n.m." exactly when unavailable.
- Do NOT add any text before or after the Table in this section.


SECTION 2 — COMMENTARY
- After the Table, add a single blank line, then a heading line: Summary / Interpretation
- Write a tight, 8-9 bullet narrative  (no colons) complementing the numbers in the table above, flagging what matters for credit. Each bullet should explain the trend of each item over the years and also mention the reason behind change in numbers (e.g. Revenue improved from £2.5m in FY21 to £7m in FY23, attributed to increase in……)
- Use financial statements to write these bullet points, especially the following sections: 'Primary Activity' and 'Business Review' and 'Financial Review' and 'Bank Debt/Borrowings/Creditors' and 'Going Concern' and other sections, 
- The bullet points should be based on the following topics:
   1. Revenue change and reasoning
   2. Gross profit movement and reasoning
   3. EBITDA change and reasoning
   4. Net working capital change and major line items driving the movement
   5. Capex development and reasoning
   6. CFADS changes and reasoning
   7. Other investing cash flow (only include if it is high for any year and the reasoning for it)
   8. Financing cash flow dynamics and reasoning for changes (e.g. increase in debt issuance, or debt repayment etc.)
   9. Total debt and leverage trend and reasoning.
- Commentary bullets must be detailed, in proper full sentences. Make sure each bullet point explains the trend and reasoning, not just restating the table (e.g. revenue increased from x to y from FY21 to FY23.)
- AVOID sub-headings and semi-colons
- Write each bullet so a reader unfamiliar with the company can clearly understand the drivers and implications
- If any information/reasoning regarding any topic of the bullet points is unavailable, please do not include it, rather than including wrong/inaccurate information
- Base all points strictly on the Table values; do not invent numbers.


SECTION 3 - SOURCES
- After the SUMMARY / INTERPRETATION, add a single blank line, then a heading line: Sources


- Point out all the sources used by the original input with the correct number index like [#6], and CITE THE COMPLETE SOURCE like which report it was used, etc.




Formatting example (shape only; values are illustrative):


| Metric | FY24 | FY23 | FY22 |
| --- | --- | --- | --- |
| Revenue (Turnover) | £576.8m [#2] | £81.4m [#6] | £32.8m [#5] |
| Revenue growth % (yoy) | +608.6% [#2][#6] | +148.0% [#5] | n.a. |
| Gross profit | n.a. | £48.4m [#3][#6] | £14.3m [#3] |


Summary / Interpretation
- Brief point 1…
- Brief point 2…
- Brief point 3…


Sources
- Source 1...
"""

capital_structure_formatting_2 = """
Return THREE sections in this exact order:


- Add a single blank line, then a heading line: 7. Capital Structure


SECTION 1 — TABLE
- header (only 2 columns): Metric, FY-latest year available example: FY-24
- CRITICAL: Display ONLY the latest fiscal year (e.g., FY24). Do NOT include FY23, FY22, or any prior years even if they appear in the source data.
- One data row per each debt facility (including one for lease liability), Gross external debt, Cash, Net external debt, Liquidity, EBITDA, Leverage. There should be 4 columns, Facility Name/Other metric, Interest Rate, Maturity, Amount (£x.xm)
- Use the following canonical metric names (match exactly when present in the source)to provide the table:
 * Facility Name (including lease liabilities) - Row (multiple rows depending on the number of facilities)
 * Interest Rate - Column 
 * Maturity - Column
 * Amount Outstanding - Column
 * Gross External Debt - Row
 * Closing Cash - Row
 * Net external debt - Row 
 * Liquidity - Row 
 * EBITDA/Adjusted EBITDA - Row
 * Leverage - Row 
- Use "n.a." / "n.m." exactly when unavailable or not meaningful.
- Always append source indices to numeric values like: £171.9m [#10] or 9.6x [#10].
- If a total is shown explicitly in the source (e.g., “Bank loans + RCF outstanding (excl. leases)”), include it. If it is not shown and all needed components are present (e.g., Facility B1 + Facility B2 + RCF drawn), you may compute it and include the computed total; otherwise use "n.a.".
- If EBITDA or Net External Debt is ≤ 0, set Leverage (Net Debt/EBITDA) to "n.m.".
- As a matter of checking accuracy, the leverage in capital structure should match the leverage of the latest year in the financial highlights table, because both are the same values



SECTION 2 — COMMENTARY
- After the Table, add a single blank line, then a heading line: Summary / Interpretation
- Write a tight, 6-7 bullet narrative (no colons) complementing the numbers in the table above, flagging what matters for credit. The bullet points should be insightful adding context to the table, so it doesn’t look like the table is repeated in text
- Use financial statements to write these bullet points, especially the following sections: 'Primary Activity' and 'Business Review' and 'Financial Review' and 'Bank Debt/Borrowings/Creditors' and 'Going Concern' and other sections
- The bullet points should be based on the following topics:
   1. Net debt and leverage trend and reasoning for changes
   2. Recent refinancing actions carried out in the past 1-2 years
   3. Debt covenants including actual covenant terms and any recent covenant tests.
   4. Debt security including collateral and security package set against the drawn secured debt
   5. Liquidity position including cash, committed undrawn facilities, overdraft, and uncommitted accordion if available.
   6. Upcoming maturities and headroom.
- Commentary bullets must be detailed, in proper full sentences
- AVOID sub-headings and semi-colon
- Each commentary bullet must be written clearly enough for a reader unfamiliar with the company to understand the meaning, impact, and implications
- If any information regarding any bullet point is unavailable, please do not include it, rather than including wrong information
- Base all points strictly on the Table values; do not invent numbers.

SECTION 3 — SOURCES
- After the SUMMARY / INTERPRETATION, add a single blank line, then a heading line: Sources
- List all sources cited in the Table with their bracket numbers (e.g., [#10]).
- For each, include a brief description: document title, section/page (if available), and what it substantiates.
- Keep one source per line.


Formatting example (shape only; values are illustrative - NOTE: Only ONE year column):


| Debt Facility | Interest Rate | Maturity | Amount Outstanding (£m)|
| --- | --- | --- | --- |
| £100m RCF | EURBIOR + 5.00% | Jun-27 | £101.2m |
| £200m Senior Secured Notes | 8.75% | Aug-29 | £205.1m |
| Lease Liability | - | - | £15.0m |
| Gross External Debt | - | - | £321.3m |
| Closing Cash | - | - | £50.0m |
| Net External Debt | - | - | £271.3m |
| Liquidity (cash + undrawn facilities) | - | - | £100.0m |
| EBITDA | - | - | £25.0m |
| Leverage | - | - | 10.9x |



Summary / Interpretation
- Brief point 1…
- Brief point 2…
- Brief point 3…


Sources
- [#1] Title / section / page — what it supports.
- [#4] Title / section / page — what it supports.
- [#10] Title / section / page — what it supports.
"""



