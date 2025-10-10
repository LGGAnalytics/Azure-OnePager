finance_formatting = """ 
Return TWO sections in this exact order:

SECTION 1 — CSV TABLE
- Output a valid CSV with header: Metric,FY24,FY23,FY22
- One data row per metric.
- Use "n.a." / "n.m." exactly when unavailable.
- CSV rules:
  * Separate fields with commas only (no extra spaces around commas).
  * Wrap any field that contains commas, brackets, percent signs, currency symbols, or spaces in double quotes.
  * Escape any internal double quotes by doubling them.
- Do NOT wrap the CSV in code fences.
- Do NOT add any text before or after the CSV in this section.

SECTION 2 — SUMMARY / INTERPRETATION
- After the CSV, add a single blank line, then a heading line: Summary / Interpretation
- Provide 3–6 concise bullets explaining the key movements, relationships, and caveats.
- Base all points strictly on the CSV values; do not invent numbers.

SECTION 3 - SOURCES
- Point out all the sources used by the original input with the correct number index like [#6], and CITE THE COMPLETE SOURCE like which report it was used, etc.


Formatting example (shape only; values are illustrative):

Metric,FY24,FY23,FY22
"Revenue (Turnover)","£576.8m [#2]","£81.4m [#6]","£32.8m [#5]"
"Revenue growth % (yoy)","+608.6% [#2][#6]","+148.0% [#5]","n.a."
"Gross profit","n.a.","£48.4m [#3][#6]","£14.3m [#3]"

Summary / Interpretation
- Brief point 1…
- Brief point 2…
- Brief point 3…
"""

stakeholders_formatting = """ 
Return TWO sections in this exact order:

SECTION 1 — CSV TABLE
- Output a valid CSV with header: Metric,Shareholders
- One data row per metric.
- Use "n.a." / "n.m." exactly when unavailable.
- CSV rules:
  * Separate fields with commas only (no extra spaces around commas).
  * Wrap any field that contains commas, brackets, percent signs, currency symbols, or spaces in double quotes.
  * Escape any internal double quotes by doubling them.
- Do NOT wrap the CSV in code fences.
- Do NOT add any text before or after the CSV in this section.

SECTION 2 — SUMMARY / INTERPRETATION
- After the CSV, add a single blank line, then a heading line: Summary / Interpretation
- Provide 3–6 concise bullets explaining the key movements, relationships, and caveats.
- Base all points strictly on the CSV values; do not invent numbers.

SECTION 3 - SOURCES
- Point out all the sources used by the original input with the correct number index like [#6], and CITE THE COMPLETE SOURCE like which report it was used, etc.


Formatting example (shape only; values are illustrative):

Metric,Shareholders
"Shareholders", "Scott"
"Management","n.a."
"Lenders","Maria"
"Auditors","James"
"Advisors","n.a."

Summary / Interpretation
- Brief point 1…
- Brief point 2…
- Brief point 3…
"""

capital_structure_formatting = """
Return THREE sections in this exact order:

SECTION 1 — CSV TABLE
- Output a valid CSV with header: Metric,FY24,FY23,FY22
- One data row per metric.
- Use the following canonical metric names (match exactly when present in the source):
  * Facility Name
  * Interest Rate
  * Maturity
  * Adjusted EBITDA
  * Cash (Closing Cash)
  * Net Debt
  * Liquidity
  * Leverage (Net Debt/EBITDA)
  * Facility B1 outstanding (GBP)
  * Facility B2 outstanding (GBP)
  * RCF drawn
  * RCF facility size
  * Delayed Drawdown Facility size
  * Bank loans due after >5 years
  * Bank loans due within 1 year
  * Bank loans + RCF outstanding (excl. leases)
- Use "n.a." / "n.m." exactly when unavailable or not meaningful.
- Always append source indices to numeric values like: £171.9m [#10] or 9.6x [#10].
- CSV rules:
  * Separate fields with commas only (no spaces around commas).
  * Wrap any field that contains spaces, commas, brackets, percent signs, currency symbols, or minus signs in double quotes.
  * Escape internal double quotes by doubling them.
- Do NOT wrap the CSV in code fences.
- Do NOT add any text before or after the CSV in this section.
- If a total is shown explicitly in the source (e.g., “Bank loans + RCF outstanding (excl. leases)”), include it. If it is not shown and all needed components are present (e.g., Facility B1 + Facility B2 + RCF drawn), you may compute it and include the computed total; otherwise use "n.a.".
- If EBITDA is ≤ 0, set Leverage (Net Debt/EBITDA) to "n.m.".

SECTION 2 — SUMMARY / INTERPRETATION
- After the CSV, add a single blank line, then a heading line: Summary / Interpretation
- Provide 3–6 concise bullets highlighting leverage, maturity profile, facility mix, liquidity lines, and visible gaps.
- Base all points strictly on the CSV values; do not invent numbers.

SECTION 3 — SOURCES
- List all sources cited in the CSV with their bracket numbers (e.g., [#10]).
- For each, include a brief description: document title, section/page (if available), and what it substantiates.
- Keep one source per line.

Formatting example (shape only; values are illustrative):

Metric,FY24,FY23,FY22
"Name of Facility","n.a","James","Scott"
"Interest Rate","n.a.","34","30"
"Maturity","30-nov","23-Dec","n.a."
"Adjusted EBITDA","n.a.","£17.9m [#10]","n.a."
"Cash (Closing Cash),"£30.0m [#4]","£30.0m [#8]","n.a."
"Net External Debt","n.a.","£171.9m [#10]","n.a."
"Leverage (Net Debt/EBITDA)","n.a.","9.6x [#10]","n.a."
"Facility B1 outstanding (GBP)","n.a.","£36.0m [#1]","n.a."
"Facility B2 outstanding (GBP)","n.a.","£135.0m [#1]","n.a."
"RCF drawn","n.a.","£16.0m [#4]","£16.0m [#8]"
"RCF facility size","n.a.","£30.0m [#4]","£30.0m [#8]"
"Delayed Drawdown Facility size","n.a.","£75.0m [#4]","£75.0m [#8]"
"Bank loans due after >5 years","n.a.","£168.7m [#1]","n.a."
"Bank loans due within 1 year","n.a.","£14.7m [#1]","n.a."
"Bank loans + RCF outstanding (excl. leases)","n.a.","£187.0m [#1][#4]","n.a."

Summary / Interpretation
- Brief point 1…
- Brief point 2…
- Brief point 3…

Sources
- [#1] Title / section / page — what it supports.
- [#4] Title / section / page — what it supports.
- [#10] Title / section / page — what it supports.
"""

business_overview_formatting = """
 - This section provides a high-level overview on what the company does, its operations, locations, products, customers and any ongoing debt/financial issues, in a bullet point format consisting of 5-6 bullet points with sentences, using the latest available annual reports/financial statements of the company 
-- Include 1-2 bullet point sentences on what the company does 
-- Include 1 bullet point on the products/services the company offers 
-- Include 1 bullet point on where the company has its operations (e.g. manufacturing facilities, operating plants, offices, customers) 
-- Include 1 bullet point on who are the customers of the company  
-- Include 1 bullet point on stress triggers of the company (e.g., 40% revenue from top 1 customer; high fixed costs; collateral shortfall; aggressive capex; covenant breach; dropping profitability; mass lay-offs etc.) 

- Each bullet must begin with the company name, "The company", or “It”. Make sure each bullet point is a proper sentence, which do not contain any sub-headings, colon or semi-colons 

- Sources to be used for this section:  
-- The bullet points regarding what the company does, its products/services, operations, customers can be sourced from the Primary Activity, Business Review, Introduction or Strategic Report section of the report 
-- The bullet point regarding company’s stress triggers can be sourced from the Business Review or Ongoing Concern or Bank Debt/Borrowings/Creditors section of the report 
-- If any of the above source suggestions does not return results for any part, please scan and check other sections of the reports to see if relevant information can be found 
 
- Notes for this section: 
-- If information for any of the bullet point is not available in the report, do not include that specific bullet point as incorrect information is strictly prohibited 

"""

# ====================== FORMATTING FOR WEBSITE DISPLAY

capital_structure_formatting_2 = """
Return THREE sections in this exact order:

SECTION 1 — TABLE
- header: Metric,FY24,FY23,FY22
- One data row per metric.
- Use the following canonical metric names (match exactly when present in the source):
  * Facility Name
  * Interest Rate
  * Maturity
  * Adjusted EBITDA
  * Cash (Closing Cash)
  * Net Debt
  * Liquidity
  * Leverage (Net Debt/EBITDA)
  * Facility B1 outstanding (GBP)
  * Facility B2 outstanding (GBP)
  * RCF drawn
  * RCF facility size
  * Delayed Drawdown Facility size
  * Bank loans due after >5 years
  * Bank loans due within 1 year
  * Bank loans + RCF outstanding (excl. leases)
- Use "n.a." / "n.m." exactly when unavailable or not meaningful.
- Always append source indices to numeric values like: £171.9m [#10] or 9.6x [#10].
- If a total is shown explicitly in the source (e.g., “Bank loans + RCF outstanding (excl. leases)”), include it. If it is not shown and all needed components are present (e.g., Facility B1 + Facility B2 + RCF drawn), you may compute it and include the computed total; otherwise use "n.a.".
- If EBITDA is ≤ 0, set Leverage (Net Debt/EBITDA) to "n.m.".

SECTION 2 — SUMMARY / INTERPRETATION
- After the Table, add a single blank line, then a heading line: Summary / Interpretation
- Provide 3–6 concise bullets highlighting leverage, maturity profile, facility mix, liquidity lines, and visible gaps.
- Base all points strictly on the Table values; do not invent numbers.

SECTION 3 — SOURCES
- List all sources cited in the Table with their bracket numbers (e.g., [#10]).
- For each, include a brief description: document title, section/page (if available), and what it substantiates.
- Keep one source per line.

Formatting example (shape only; values are illustrative):

Metric                                      | FY24        |FY23              | FY22
Name of Facility                            | n.a         | James            | Scott
Interest Rate                               | n.a.        | 34               | 30
Maturity                                    | 30-nov      | 23-Dec           | n.a.
Adjusted EBITDA                             | n.a.        | £17.9m [#10]     | n.a.
Cash (Closing Cash)                         | £30.0m [#4] | £30.0m [#8]      | n.a.
Net External Debt                           | n.a.        | £171.9m [#10]    | n.a.
Leverage (Net Debt/EBITDA)                  | n.a.        | "9.6x [#10]      | n.a.
Facility B1 outstanding (GBP)               | n.a.        | "£36.0m [#1]     | n.a.
Facility B2 outstanding (GBP)               | n.a.        | "£135.0m [#1]    | n.a.
RCF drawn                                   | £30.0m [#4] | £16.0m [#4]      | £16.0m [#8]
RCF facility size                           | n.a.        | £30.0m [#4]      | £30.0m [#8]
Delayed Drawdown Facility size              | n.a.        | £75.0m [#4]      | £75.0m [#8]
Bank loans due after >5 years               | n.a.        | £168.7m [#1]     | n.a.
Bank loans due within 1 year                | n.a.        | £14.7m [#1]      | n.a.
Bank loans + RCF outstanding (excl. leases) | n.a.        | £187.0m [#1][#4] | n.a.

Summary / Interpretation
- Brief point 1…
- Brief point 2…
- Brief point 3…

Sources
- [#1] Title / section / page — what it supports.
- [#4] Title / section / page — what it supports.
- [#10] Title / section / page — what it supports.
""" 

stakeholders_formatting_2 = """ 
Return TWO sections in this exact order:

SECTION 1 — TABLE
- Table header: Metric,Shareholders
- One data row per metric.
- Use "n.a." / "n.m." exactly when unavailable.
- Do NOT add any text before or after the Table in this section.

SECTION 2 — SUMMARY / INTERPRETATION
- After the Table, add a single blank line, then a heading line: Summary / Interpretation
- Provide 3–6 concise bullets explaining the key movements, relationships, and caveats.
- Base all points strictly on the Table values; do not invent numbers.

SECTION 3 - SOURCES
- Point out all the sources used by the original input with the correct number index like [#6], and CITE THE COMPLETE SOURCE like which report it was used, etc.


Formatting example (shape only; values are illustrative):

Metric       | Shareholders
Shareholders | Scott
Management   | n.a.
Lenders      | Maria
Auditors     | James
Advisors     | n.a.

Summary / Interpretation
- Brief point 1…
- Brief point 2…
- Brief point 3…
"""

finance_formatting_2= """ 
Return TWO sections in this exact order:

SECTION 1 — TABLE
- Output a valid Table with header: Metric,FY24,FY23,FY22
- One data row per metric.
- Use "n.a." / "n.m." exactly when unavailable.
- Do NOT add any text before or after the Table in this section.

SECTION 2 — SUMMARY / INTERPRETATION
- After the Table, add a single blank line, then a heading line: Summary / Interpretation
- Provide 3–6 concise bullets explaining the key movements, relationships, and caveats.
- Base all points strictly on the Table values; do not invent numbers.

SECTION 3 - SOURCES
- Point out all the sources used by the original input with the correct number index like [#6], and CITE THE COMPLETE SOURCE like which report it was used, etc.


Formatting example (shape only; values are illustrative):

Metric                  |   FY24                |   FY23            |   FY22
Revenue (Turnover)      |   £576.8m [#2]        |   £81.4m [#6]     |   £32.8m [#5]
Revenue growth % (yoy)  |   +608.6% [#2][#6]    |   +148.0% [#5]    |   n.a.
Gross profit            |   n.a.                |   £48.4m [#3][#6] |   £14.3m [#3]"

Summary / Interpretation
- Brief point 1…
- Brief point 2…
- Brief point 3…
"""