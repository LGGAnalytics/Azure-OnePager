system_mod= """
You are a restructuring analyst focused on identifying companies in financial distress that could be advisory targets for your company. You answer questions regarding the company's business overview, its recent key developments, its stakeholders, its financial performance and its capital structure. You rely on the latest three annual reports and financial statements of companies, as well as Web Search to answer these questions. 
Key points: 
Business Overview: 
- Talk about what the company does, products/services the company offers, where the company has its operations (e.g. manufacturing facilities, operating plants, offices, customers), who are the customers of the company, stress triggers of the company (e.g., 40% revenue from top 1 customer; high fixed costs; collateral shortfall; aggressive capex; covenant breach; dropping profitability; mass lay-offs etc.), any latest Credit Ratings from Moody’s, S&P and Fitch, if available (e.g. Fitch rated Company BBB+/Stable; Moody’s rated Company B-/Negative etc.)
Key Developments: 
- The latest 8-10 available news of the company in reverse chronological order of release date, using Web Search, complemented by annual reports/financial statements 
- Following news are priority, other news must not be included: (1) Debt issuance or debt refinancing (2) Restructuring, (3) Mergers/Acquisitions/Divestments, (5) Changes in management personnel, (6) Facility openings/closures, (7) Strategic partnerships, (8) Dividends payment/Share repurchase etc. 
Stakeholders: 
- Provide key stakeholders of the company, including the following, using the available annual reports/financial statements of the company, as well as Web Search 
-- Shareholders (Immediate and Ultimate parent company if a private company) 
-- Management: Chariman, CEO and CFO (Directors if a private company) 
-- Lenders 
-- Advisors (Legal Advisor, Financial Advisor, Bankers, Solicitors, Auditors) 
Financial Performance: 
- Look into the financial performance for the last three years of the target company. You can highlight key metrics and suggest the reasoning for changes over the years. Key metrics include: -- Revenue (Use Income Statement – Always Given) 
-- Gross Profit (Use Income Statement – Always Given): Revenue – Cost of Goods Sold (ONLY use this formula if the report does not already provide the gross profit value) 
-- EBITDA (Check all sections of the report, EBITDA or Adjusted EBITDA might be provided – If not provided, calculate manually): Operating Profit + Depreciation and Amortization (ONLY use this formula if the report does not already provide the EBITDA/Adjusted EBITDA value) 
-- Revenue Growth % (Always Calculate Manually): (RevenueT0÷RevenueT-1)-1 
-- Gross Margin % (Always Calculate Manually): Gross Profit / Revenue 
-- EBITDA Margin % (Always Calculate Manually): EBITDA / Revenue (put n.m. if it is negative) 
-- Cash Flow from Operating Activities excl. Net Working Capital (Use Cash Flow Statement – Always Calculate Manually): Net Cash Flow from Operating Activities – Net Working Capital (Net Working Capital should be the one calculated below) 
-- Net Working Capital (Use Cash Flow Statement – Always Calculate Manually): Increase/Decrease in Debtors/Receivables + Increase/Decrease in Inventory/Stock + Increase/Decrease in Creditors/Payables (These values are usually provided under Cash flows from Operating Activities section of Cash Flow Statement and should be used as it is for calculation (do not change its signs e.g. change from negative to positive)) 
-- Capex (Use Cash Flow Statement – Always Calculate Manually): Acquisition of Property, Plant, Equipment/Tangible Assets + Acquisition of Intangible Assets (These values are usually provided under Cash flows from Investing Activities section of Cash Flow Statement) 
-- Other Cash Flow from Investing Activities (Use Cash Flow Statement – Always Calculate Manually): Net Cash Flow from Investing Activities – Capex (Capex should be the one calculated above) 
-- CFADS (Use Cash Flow Statement – Always Calculate Manually): Net Cash Flow from Operating Activities + Net Cash Flow from Investing Activities (Both of these values are always provided in the Cash Flow Statement) 
-- Cash Flow from Financing Activities (Use Cash Flow Statement – Always Given): This should include the breakdown of sub-items and their contribution to this net number e.g. debt repayment, debt issuance, share issuance etc. 
-- Opening Cash (Use Cash Flow Statement – Always Given) 
-- Change in Cash (Use Cash Flow Statement – Always Given) 
-- Closing Cash (Use Cash Flow Statement – Always Given) 
-- Total Debt (From Debt or Bank Debt or Borrowings or Creditors section – Always Calculate Manually): Bank Debt + Lease Liabilities (This only includes external debt e.g. bank loans, bonds, RCFs etc. and lease liabilities (only financial leases, not operating leases), and no internal debt (e.g. shareholder loans, loans from related parties, loans from subsidiaries etc.))
-- Net Debt (Always Calculate Manually): Net Debt: Total Debt – Closing Cash 
-- Leverage (Always Calculate Manually): Net Debt / EBITDA (put n.m. if it is negative) 
- Note: Use Income Statement, Cash Flow Statement and Financial Statement Notes sections of the annual reports for financial performance calculations 
Capital Structure: 
- Look into the capital structure for the latest year, Highlight key metrics including Debt facilities with the following columns: 
-- Name of the Facility (e.g. £300m Term loan, $200m RCF, £100m Senior Secured Notes etc.) 
-- Interest Rate (e.g. 5.25%, EURIBOR + 3.75% etc.) 
-- Maturity (This is the latest repayment date of the debt facility. It should be provided in the format mmm-yy e.g. Jun-25) 
-- Amount Outstanding (Provide it in millions, rounded to 1 decimal point e.g. £1.2m) 
- Lease liabilities is also counted as a debt facility (only financial leases, no operational leases). Internal loans such as Shareholder loans, loans from related parties, loans from subsidiaries MUST never be included. 
- The table must also contain the following rows: 
-- Gross External Debt (Sum of amount outstanding for all debt facilities) 
-- Cash (Closing Cash) -- Net External Debt (Gross Debt – Closing Cash) 
-- Liquidity (Closing cash + any undrawn facilities, e.g. undrawn amount of RCF, credit lines or overdrafts). Provide this in millions, rounded to 1 decimal place (e.g. £1.2m) 
-- EBITDA 
-- Leverage (Net Debt / EBITDA) - Interesting things you can highlight regarding capital structure: (1) Net debt and leverage trend, with underlying factors, (2) Recent refinancing actions, (3) Debt covenants pressure (list key covenants (net leverage, interest coverage, fixed charge coverage etc.) and if there was a breach or there is a likelihood of breach, according to tests), (4) Debt security including collateral and security package, (5) Liquidity position, stating cash on hand, committed undrawn facilities, overdraft capacity, and any accordion (expansion) options if available, (6) Nearest material bond/loan maturities, committed/uncommitted facilities, ability to refinance, (7) Debt outlook (only if mentioned in credit ratings report by Moody’s, S&P and Fitch) 
- Notes: The data is available in Debt or Bank Debt or Borrowings or Creditors section Financial Statement Notes in the annual reports
General Formatting Rules: 
- Always use the latest three available annual reports/financial statements of the company, as well as Web Search(e.g. 2024, 2023 and 2022). In case if not all three are available, suggest please 
- Provide sources for each question answered. The exact page numbers of the report used for each section, as well as source links (if web search is used for that part) must be mentioned, or even in-line citation if possible, so it can be referenced back for accuracy purposes. 
- Always write dates in the format "Mmm-yy" (e.g. Jun-24), fiscal years as "FYXX" (e.g. FY24, LTM1H25), and currencies in millions in the format "£1.2m" 
- Provide n/a instead of incorrect information 
Other Important information: 
- Answer any other questions asked about the company to your best ability
- Some examples of key triggers and considerations for answers include:
-- Depleting Liquidity
-- Covenants Breach
-- Refinancing Risks
-- Falling Profitability
-- Restructuring
-- Imminent/Concentrated Maturities
-- Large Customer or Supplier Concentration (e.g., >30–40% revenue from one customer) — revenue / supply shock risk
-- Collateral Shortfall or Weak Security Package — unsecured creditors at risk
-- Rising Interest Rates / Mark-to-Market Funding Costs — higher service costs and covenant pressure
-- Negative or Volatile Cash Flows / CFADS Decline — impaired debt service capability
-- Material Asset Impairments or Write-downs — equity wipeout and covenant impacts
-- Major Capex Overruns or Aggressive Capital Spending — cash drains and margin compression
-- Supply-Chain Disruption or Single-source Suppliers — operational continuity risk
-- Credit Rating Downgrade or Watchlist Placement — access to markets constrained, higher funding costs
-- Cross-default or Intercompany Guarantees — contagion across facilities / group entities
-- Mass Layoffs / Key Management Turnover — signalling distress and execution risk
-- Fraud, Governance Failures or Related-party Transactions — heightened legal/contractual risk
"""

section1 = """
"""

section2 = """
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
|
"""

section2_json = {
    "filters": {
        "company_name": ""
    },
    "sections": {
        "overview": {
            "queries": [
                "business overview primary activity",
                "strategic report introduction",
                "business review company description",
            ],
            "min_hits": 5,
        },
        "products_services": {
            "queries": [
                "products services offerings portfolio",
                "product lines service lines",
            ],
            "min_hits": 3,
        },
        "operations_footprint": {
            "queries": [
                "operations locations facilities plants offices",
                "manufacturing distribution footprint",
                "geographic segments operations by region",
            ],
            "min_hits": 3,
        },
        "customers": {
            "queries": [
                "customers client base key customers end markets",
                "sales channels customer concentration",
            ],
            "min_hits": 3,
        },
        "stress_triggers": {
            "queries": [
                "going concern material uncertainty liquidity",
                "borrowings creditors bank debt covenants leverage",
                "debt maturity profile interest coverage",
                "impairment restructuring cost reduction layoffs",
            ],
            "min_hits": 4,
        },
    },
    "backoff_rules": {
        "if_section_hits_below": 2,
        "broaden_to": [
            {"drop_adj_keep_nouns": True},
            {"add_alt_terms": {
                "borrowings": ["loans", "debt", "notes payable"],
                "customers":  ["revenue by customer", "concentration"],
                "going concern": ["viability statement", "liquidity risk"],
            }},
        ],
    },
}

section3 = """
"""

section4 = """
"""

section5 = """
"""

section6 = """
6. Key Stakeholders: 

- This section provides key stakeholders of the company in a table format, including the following, using the available annual reports/financial statements of the company: 
-- Shareholders (Provide the immediate parent company and ultimate parent company of the target company in the case of a private company. In the case of a public company, provide top 5 shareholders of the company with % owned) 
-- Management (Include the name of the chairman, Chief Executive Officer and Chief Financial Officer. If these three are not available provide the name of the Directors listed in the report) 
-- Lenders (Include the name of the lenders of the company for each of the debt facility, if reported) 
-- Auditors (Provide the name of the auditor of the company mentioned in the report, e.g. PwC, EY etc.) 
-- Advisors (Provide any financial or legal advisors, solicitors or bankers listed in the report) 

 
- Sources to be used for this section:  
-- Shareholders will be available under the Parent Company section of the report, or throughout text in different sections, for private companies. For public limited companies, the top shareholders will be listed in the Shareholders section of the report 
-- Management will be available in Company Information or Strategic Report or Key Management or Board of Directors section of the report 
-- Lenders will be available in the Notes section of the report, particularly in the Bank Debt or Debt or Borrowings or Payables or Creditors section of the report 
-- Auditors will be available in the Company Information or Independent Auditors Report section of the report 
-- Advisors will be available in the Company Information section of the report 
-- If any of the above source suggestions does not return results for any part, please scan and check other sections of the reports to see if relevant information can be found 

 
- Notes for this section: 
-- If for any of the part there isn’t information from the annual report/financial statements, put n/a instead of providing wrong/inaccurate information 
"""

section6_json = {
    "filters": {
        "company_name": ""
    },
    "sections": {
        # Run both shareholders branches; in generation, prefer the branch with stronger evidence.
        "shareholders_private": {
            "queries": [
                "immediate parent ultimate parent ownership structure",
                "group structure parent company ownership",
                "related parties parent undertaking controlling party",
            ],
            "min_hits": 3,
        },
        "shareholders_public": {
            "queries": [
                "top shareholders major shareholders significant shareholders % ownership",
                "shareholder register share capital ownership analysis",
                "substantial shareholdings holdings above 3%",
            ],
            "min_hits": 4,
        },
        "management": {
            "queries": [
                "board of directors company information",
                "chairman chief executive officer ceo chief financial officer cfo",
                "key management personnel senior management directors",
            ],
            "min_hits": 4,
        },
        "lenders": {
            "queries": [
                "borrowings bank debt loans creditors loan facilities",
                "revolving credit facility term loan maturity profile lenders",
                "loan agreement facility agent syndicate lenders noteholders bondholders",
            ],
            "min_hits": 5,
        },
        "auditors": {
            "queries": [
                "independent auditor's report auditor appointed auditors",
                "report of the independent auditors",
                "auditor's opinion audit firm",
            ],
            "min_hits": 2,
        },
        "advisors": {
            "queries": [
                "company information advisors solicitors bankers",
                "financial advisor legal advisor corporate broker nominated adviser",
                "sponsors reporting accountants",
            ],
            "min_hits": 2,
        },
    },
    "backoff_rules": {
        "if_section_hits_below": 2,
        "broaden_to": [
            {"drop_adj_keep_nouns": True},
            {"add_alt_terms": {
                "shareholders": ["ownership", "equity holders", "share register"],
                "management": ["executive directors", "non-executive directors", "leadership"],
                "lenders": ["bank loans", "loan notes", "debentures", "secured loans", "RCF", "TLB"],
                "auditors": ["audit report", "auditor's report", "registered auditor"],
                "advisors": ["counsel", "solicitor", "bankers", "corporate finance advisor"],
            }},
        ],
    },
}


section7 = """
7. Financial Highlights: 

- This section looks into the financial performance for the last three years of the target company. This section has two parts, the first one is a table with numbers related to the financial performance of the company, while the second part is the bullet-point commentary complementing the table. 
   
- The first part includes a table with the following financial information for the last three years, using the last three available annual reports/financial statements of the company. It should have rows (some of which are provided and some of which have to be calculated using provided formulae) including: 
-- Revenue (Use Income Statement – Always Given) 
-- Gross Profit (Use Income Statement – Always Given): Revenue – Cost of Goods Sold (ONLY use this formula if the report does not already provide the gross profit value) 
-- EBITDA (Check all sections of the report, EBITDA or Adjusted EBITDA might be provided – If not provided, calculate manually): Operating Profit + Depreciation and Amortization (ONLY use this formula if the report does not already provide the EBITDA/Adjusted EBITDA value) 
-- Revenue Growth % (Always Calculate Manually): (RevenueT0÷RevenueT−1)−1 
-- Gross Margin % (Always Calculate Manually): Gross Profit / Revenue 
-- EBITDA Margin % (Always Calculate Manually): EBITDA / Revenue (put n.m. if it is negative) 
-- Cash Flow from Operating Activities excl. Net Working Capital (Use Cash Flow Statement – Always Calculate Manually): Net Cash Flow from Operating Activities – Net Working Capital (Net Working Capital should be the one calculated below) 
-- Net Working Capital (Use Cash Flow Statement – Always Calculate Manually): Increase/Decrease in Debtors/Receivables + Increase/Decrease in Inventory/Stock + Increase/Decrease in Creditors/Payables (These values are usually provided under Cash flows from Operating Activities section of Cash Flow Statement and should be used as it is for calculation (do not change its signs e.g. change from negative to positive)) 
-- Capex (Use Cash Flow Statement – Always Calculate Manually): Acquisition of Property, Plant, Equipment/Tangible Assets + Acquisition of Intangible Assets (These values are usually provided under Cash flows from Investing Activities section of Cash Flow Statement) 
-- Other Cash Flow from Investing Activities (Use Cash Flow Statement – Always Calculate Manually): Net Cash Flow from Investing Activities – Capex (Capex should be the one calculated above) 
-- CFADS (Use Cash Flow Statement – Always Calculate Manually): Net Cash Flow from Operating Activities + Net Cash Flow from Investing Activities (Both of these values are always provided in the Cash Flow Statement) 
-- Cash Flow from Financing Activities (Use Cash Flow Statement – Always Given): This should include the breakdown of sub-items and their contribution to this net number e.g. debt repayment, debt issuance, share issuance etc. 
-- Opening Cash (Use Cash Flow Statement – Always Given) 
-- Change in Cash (Use Cash Flow Statement – Always Given) 
-- Foreign Exchange Effect (Use Cash Flow Statement – Always Given) 
-- Closing Cash (Use Cash Flow Statement – Always Given) 
-- Total Debt (From Debt or Bank Debt or Borrowings or Creditors section – Always Calculate Manually): Bank Debt + Lease Liabilities (This only includes external debt e.g. bank loans, bonds, RCFs etc. and lease liabilities (only financial leases, not operating leases), and no internal debt (e.g. shareholder loans, loans from related parties, loans from subsidiaries etc.))  
-- Net Debt (Always Calculate Manually): Net Debt: Total Debt – Closing Cash 
-- Leverage (Always Calculate Manually): Net Debt / EBITDA (put n.m. if it is negative) 
 
- For the table, provide data from the last three fiscal years (e.g. FY22, FY23, FY24). All values must be shown in millions, rounded to 1 decimal point (e.g. £1.2m). Leverage must be reported in the following format e.g. 1.2x. Show the values as they are reported and calculated e.g. If capex is in negative, it should be reported in negative in the table. 
 
- The second part includes a bullet-point commentary on the table containing financials, explaining the movement in numbers over the years, as well as the underlying reasons behind the moves: 
-- Discuss the following topics: (1) Revenue change and key drivers, (2) Gross profit movement and explanation, (3) EBITDA direction and reasons, (4) Net working capital change and major line items driving the movement, (5) Capex development, (6) CFADS directions and reasons, (7) Financing cash flow dynamics including increase/decrease in dividends, debt repayments, and issuances, (8) Total debt and leverage trend and reasons 
-- Each bullet point must be a proper sentence discussing the movement or change in certain item over the years, as well as the reason behind the increase or decrease. Do not use semi-colons in the bullet points 
-- Write each bullet so a reader unfamiliar with the company can clearly understand the drivers and implications 
 
- Sources to be used for this section:  
-- The data for the table in the first section is available in the Income Statement section, Cash Flow Statement section as well as some specific Notes in the latest three annual reports/financial statements 
-- The information for the commentary for the second section is available in the Business Review or Financial Review section in the reports 
-- If any of the above source suggestions does not return results for any part, please scan and check other sections of the reports to see if relevant information can be found 
 
- Notes for this section: 
-- ALWAYS use the formulae and sourcing logic provided for this section, as accurate calculations are important for analysis 
-- EBITDA (EBITDA/Adjusted EBITDA) must always be checked in the annual report if it is provided directly. If it is not, then only calculate using the provided formula 
-- If cash flow statement is not available, please put n.a. for the numbers that are not available or cannot be calculated 
-- For values that are restated for a specific financial year, please always use the restated values 
-- If information on some specific topics of the commentary is not available, please do not include bullet points for them 


"""

section7_json = {
    "filters": {
        "company_name": ""
    },
    "sections": {
        # Income statement sources
        "income_statement": {
            "queries": [
                "income statement consolidated statement of profit or loss",
                "statement of comprehensive income revenue cost of sales gross profit",
                "operating profit depreciation amortisation expenses",
                "alternative performance measures ebitda adjusted ebitda non gaap",
            ],
            "min_hits": 6,
        },

        # Cash flow statement sources (operating)
        "cash_flow_operating": {
            "queries": [
                "cash flow statement net cash from operating activities",
                "working capital changes increase decrease in receivables debtors",
                "increase decrease in inventories stock",
                "increase decrease in payables creditors",
                "reconciliation of profit to cash from operations",
            ],
            "min_hits": 6,
        },

        # Cash flow statement sources (investing)
        "cash_flow_investing": {
            "queries": [
                "cash flows from investing activities",
                "purchase acquisition of property plant and equipment tangible assets",
                "purchase acquisition of intangible assets capitalised development costs",
                "proceeds disposals investments acquisitions",
                "net cash used in investing activities",
            ],
            "min_hits": 5,
        },

        # Cash flow statement sources (financing)
        "cash_flow_financing": {
            "queries": [
                "cash flows from financing activities",
                "proceeds from borrowings issue of debt",
                "repayment of borrowings debt repayment",
                "dividends paid share buyback share issuance",
                "lease payments interest paid",
            ],
            "min_hits": 5,
        },

        # Cash & FX reconciliation lines
        "cash_fx_reconciliation": {
            "queries": [
                "cash and cash equivalents opening cash closing cash",
                "effect of exchange rate changes on cash foreign exchange effect",
                "net increase decrease in cash change in cash",
            ],
            "min_hits": 4,
        },

        # Debt & leases (notes)
        "debt_and_leases_notes": {
            "queries": [
                "borrowings bank debt loans creditors interest bearing liabilities",
                "revolving credit facility rcf term loan tlb bond notes payable",
                "lease liabilities ifrs 16 finance leases",
                "maturity profile covenants security",
            ],
            "min_hits": 5,
        },

        # Restatements / accounting policy changes (to prefer restated values)
        "restatements": {
            "queries": [
                "restated figures restatement prior period adjustment",
                "reclassification comparatives revised",
                "change in accounting policy",
            ],
            "min_hits": 2,
        },

        # Narrative for commentary
        "financial_review_commentary": {
            "queries": [
                "financial review business review management discussion analysis",
                "results of operations performance overview",
                "drivers of change variance analysis revenue gross margin ebitda",
                "working capital capex cash flow commentary",
                "debt leverage liquidity discussion",
            ],
            "min_hits": 6,
        },
    },

    "backoff_rules": {
        "if_section_hits_below": 2,
        "broaden_to": [
            {"drop_adj_keep_nouns": True},
            {"add_alt_terms": {
                "income statement": ["profit and loss", "statement of operations"],
                "ebitda": ["operating profit before depreciation and amortization"],
                "receivables": ["trade receivables", "debtors"],
                "payables": ["trade payables", "creditors"],
                "inventories": ["stock"],
                "borrowings": ["interest-bearing loans and borrowings", "loans and overdrafts"],
                "lease liabilities": ["IFRS 16 liabilities", "finance leases"],
                "financial review": ["MD&A", "operating and financial review"],
            }},
        ],
    },

    # Hints for the generator/extractor stage
    "format_hints": {
        "part1": "table",     # numbers table
        "part2": "bullets",   # commentary bullets
        "table_unit": "millions",         # normalize to millions
        "table_rounding_dp": 1,           # 1 decimal place
        "year_labels": "FY",              # e.g., FY22, FY23, FY24
        "percent_rounding_dp": 1,         # e.g., 12.3%
        "leverage_suffix": "x",           # e.g., 2.1x
        "na_token": "n.a.",
        "not_meaningful_token": "n.m.",   # for negative margins/leverage
        "preserve_signs": True,           # keep negatives as reported
        "require_restated_if_available": True,
    },

    # Declarative calculation plan (deterministic)
    "calculation_rules": {
        "precedence": {
            "gross_profit": ["disclosed:gross_profit", "calc:revenue - cost_of_sales"],
            "ebitda": ["disclosed:ebitda_or_adjusted", "calc:operating_profit + depreciation + amortisation"],
        },
        "rows": [
            {"key": "revenue", "label": "Revenue", "source": "income_statement:revenue", "type": "value"},
            {"key": "gross_profit", "label": "Gross Profit", "source": "income_statement:gross_profit_or_calc", "type": "value"},
            {"key": "ebitda", "label": "EBITDA", "source": "income_statement:ebitda_or_calc", "type": "value"},
            {"key": "revenue_growth_pct", "label": "Revenue Growth %", "formula": "(revenue[t]/revenue[t-1])-1", "type": "percent", "guard": "if missing t-1 → n.a."},
            {"key": "gross_margin_pct", "label": "Gross Margin %", "formula": "gross_profit[t]/revenue[t]", "type": "percent", "guard": "if revenue<=0 → n.a.; if result<0 → n.m."},
            {"key": "ebitda_margin_pct", "label": "EBITDA Margin %", "formula": "ebitda[t]/revenue[t]", "type": "percent", "guard": "if revenue<=0 → n.a.; if result<0 → n.m."},

            {"key": "cfo", "label": "Net Cash Flow from Operating Activities", "source": "cash_flow_operating:cfo_net", "type": "value"},
            {"key": "nwc", "label": "Net Working Capital (movement)", "formula": "Δreceivables + Δinventory + Δpayables", "source": "cash_flow_operating:wk_lines", "type": "value",
             "notes": "Use signs exactly as shown in cash flow (do not flip)."},
            {"key": "cfo_excl_nwc", "label": "Cash Flow from Operating Activities excl. NWC", "formula": "cfo - nwc", "type": "value"},

            {"key": "capex", "label": "Capex", "formula": "purchase_pp&e + purchase_intangibles", "source": "cash_flow_investing:pp&e_intangibles", "type": "value"},
            {"key": "cfi", "label": "Net Cash Flow from Investing Activities", "source": "cash_flow_investing:cfi_net", "type": "value"},
            {"key": "other_cfi", "label": "Other Cash Flow from Investing Activities", "formula": "cfi - capex", "type": "value"},

            {"key": "cfads", "label": "CFADS", "formula": "cfo + cfi", "type": "value"},

            {"key": "cff", "label": "Cash Flow from Financing Activities", "source": "cash_flow_financing:cff_net", "type": "value",
             "notes": "Also capture sub-items for commentary: issuance/repayment/dividends/leases/interest."},

            {"key": "opening_cash", "label": "Opening Cash", "source": "cash_fx_reconciliation:opening_cash", "type": "value"},
            {"key": "change_in_cash", "label": "Change in Cash", "source": "cash_fx_reconciliation:net_increase_decrease", "type": "value"},
            {"key": "fx_effect", "label": "Foreign Exchange Effect", "source": "cash_fx_reconciliation:fx_effect", "type": "value"},
            {"key": "closing_cash", "label": "Closing Cash", "source": "cash_fx_reconciliation:closing_cash", "type": "value"},

            {"key": "bank_debt", "label": "Bank Debt", "source": "debt_and_leases_notes:borrowings_bank_loans_bonds", "type": "value"},
            {"key": "lease_liabilities", "label": "Lease Liabilities", "source": "debt_and_leases_notes:ifrs16_lease_liabilities", "type": "value"},
            {"key": "total_debt", "label": "Total Debt", "formula": "bank_debt + lease_liabilities", "type": "value",
             "notes": "Exclude internal debt such as shareholder/related party loans."},
            {"key": "net_debt", "label": "Net Debt", "formula": "total_debt - closing_cash", "type": "value"},

            {"key": "leverage", "label": "Leverage (Net Debt / EBITDA)", "formula": "net_debt / ebitda", "type": "ratio",
             "format": "x", "guard": "if ebitda<=0 or result<0 → n.m."},
        ],
    },

    # Narrative guidance for part 2 (your generator can use these topics)
    "commentary_topics": [
        "Revenue change and key drivers",
        "Gross profit movement and explanation",
        "EBITDA direction and reasons",
        "Net working capital change and major line items",
        "Capex development",
        "CFADS direction and reasons",
        "Financing cash flow dynamics (dividends, debt repayments/issuances)",
        "Total debt and leverage trend and reasons",
    ],

    # Data normalization & validation rules
    "normalization_rules": {
        "detect_currency": ["notes, statements, headers"],
        "detect_scale": ["'All amounts in thousands/millions' footers/headers"],
        "target_unit": "millions",
        "round_to_dp": 1,
        "apply_scale": "convert reported to millions before calculations",
        "consistent_currency_across_years": True,
        "prefer_restated_values": True,
        "missing_policy": {
            "numeric": "n.a.",
            "percent_negative_to_nm": ["gross_margin_pct", "ebitda_margin_pct"],
            "ratio_negative_to_nm": ["leverage"],
        },
    },

    # Optional: capture sub-items for richer commentary (not displayed in the main table)
    "supplemental_capture": {
        "financing_breakdown": [
            "proceeds from borrowings",
            "repayment of borrowings",
            "dividends paid",
            "issue of shares / buybacks",
            "lease payments",
            "interest paid",
        ],
        "working_capital_lines": [
            "increase/decrease in trade receivables",
            "increase/decrease in inventories",
            "increase/decrease in trade payables",
        ],
        "ebitda_variant": [
            "EBITDA",
            "Adjusted EBITDA",
            "Operating profit before depreciation and amortisation",
        ],
    },

    # Output schema hints for your renderer
    "extraction_schema": {
        "part1_table": {
            "columns": ["Metric", "FY(t-2)", "FY(t-1)", "FY(t)", "Source #[snippet]"],
            "order": [
                "Revenue",
                "Gross Profit",
                "EBITDA",
                "Revenue Growth %",
                "Gross Margin %",
                "EBITDA Margin %",
                "Cash Flow from Operating Activities excl. NWC",
                "Net Working Capital (movement)",
                "Capex",
                "Other Cash Flow from Investing Activities",
                "CFADS",
                "Cash Flow from Financing Activities",
                "Opening Cash",
                "Change in Cash",
                "Foreign Exchange Effect",
                "Closing Cash",
                "Total Debt",
                "Net Debt",
                "Leverage (Net Debt / EBITDA)",
            ],
        },
        "part2_bullets": {
            "count_range": [6, 10],
            "style": "plain sentences, no semicolons, cite [#] as needed",
        },
    },
}


section8 = """
8. Capital Structure: 
- This section looks into the capital structure for the latest years of the target company. This section has two parts, the first one is a table with capital structure of the company, while the second part is the bullet-point commentary complementing the table. 
   
- The first part includes a table with the following capital structure information for the latest year, using the available annual report/financial statement of the company. It should list out all the debt facilities with the following columns: 
-- Name of the Facility (e.g. £300m Term loan, $200m RCF, £100m Senior Secured Notes etc.) 
-- Interest Rate (e.g. 5.25%, EURIBOR + 3.75% etc.) 
-- Maturity (This is the latest repayment date of the debt facility. It should be provided in the format mmm-yy e.g. Jun-25) 
-- Amount Outstanding (Provide it in millions, rounded to 1 decimal point e.g. £1.2m) 
 
- Lease liabilities is also counted as a debt facility (only financial leases, no operational leases). Internal loans such as Shareholder loans, loans from related parties, loans from subsidiaries MUST never be included. 
 
- The table must also contain the following rows: 
-- Gross External Debt (Sum of amount outstanding for all debt facilities) 
-- Cash (Closing Cash) 
-- Net External Debt (Gross Debt – Closing Cash) 
-- Liquidity (Closing cash + any undrawn facilities, e.g. undrawn amount of RCF, credit lines or overdrafts). Provide this in millions, rounded to 1 decimal place (e.g. £1.2m) 
-- EBITDA 
-- Leverage (Net Debt / EBITDA) 
 
- Make sure debt and leverage matches the amount in the financial highlights section 
 
- For the table provide data for the latest year only. All values must be shown in millions, rounded to 1 decimal point (e.g. £1.2m) 
 
- The second part includes a bullet-point commentary on the capital structure table:  
-- Discuss the following topics: (1) Net debt and leverage trend, with underlying factors, (2) Recent refinancing actions, (3) Debt covenants pressure (list key covenants (net leverage, interest coverage, fixed charge coverage etc.) and if there was a breach or there is a likelihood of breach, according to tests), (4) Debt security including collateral and security package, (5) Liquidity position, stating cash on hand, committed undrawn facilities, overdraft capacity, and any accordion (expansion) options if available, (6) Nearest material bond/loan maturities, committed/uncommitted facilities, ability to refinance 
-- Each bullet point must be a proper sentence. Do not use semi-colons in the bullet points 
-- Write each bullet so a reader unfamiliar with the company can clearly understand the drivers and implications 
 
- Sources to be used for this section:  
-- The data in table in the first section is available in Debt or Bank Debt or Borrowings or Creditors section in the reports. Cash and EBITDA can be used from the previous Financial Highlights section of the profile 
-- For the table in the first section, specifically for information such as interest rate and maturity, please also scan the text available throughout the report as some section might mention these things 
-- The information for the commentary for the second section is available Debt or Bank Debt or Borrowings or Creditors section in the reports  
-- If any of the above source suggestions does not return results for any part, please scan and check other sections of the reports to see if relevant information can be found 
 
- Notes for this section: 
-- If only internal debt is available (no external bank debts, lease liabilities), please do not provide capital structure and indicate the reasoning 
-- If information on some specific topics of the commentary is not available, please do not include bullet points for them 
"""


section8_json = {
    "filters": {
        "company_name": ""
    },
    "sections": {
        # Core debt disclosures (names, amounts, facilities list)
        "debt_facilities_core": {
            "queries": [
                "borrowings bank debt loans creditors interest-bearing liabilities",
                "term loan tlb revolving credit facility rcf bond notes senior secured notes",
                "amount outstanding carrying amount debt facilities schedule",
            ],
            "min_hits": 6,
        },
        # Interest rate terms (margin/base rate)
        "interest_terms": {
            "queries": [
                "interest rate margin coupon euribor sofr libor + spread",
                "effective interest rate interest expense rate payable",
                "terms and conditions financing agreements",
            ],
            "min_hits": 4,
        },
        # Maturity / due dates / amortization
        "maturity_terms": {
            "queries": [
                "maturity profile contractual maturities repayment schedule",
                "final maturity due date redemption date",
                "amortisation schedule bullet maturity",
            ],
            "min_hits": 4,
        },
        # Lease liabilities (counted as a debt facility; finance leases only)
        "lease_liabilities": {
            "queries": [
                "lease liabilities ifrs 16 finance leases",
                "liabilities arising from leasing",
                "maturity analysis of lease liabilities",
            ],
            "min_hits": 3,
        },
        # Undrawn facilities / liquidity lines (e.g., RCF headroom)
        "undrawn_facilities": {
            "queries": [
                "undrawn committed facilities available headroom",
                "undrawn amount revolving credit facility overdraft capacity",
                "liquidity resources cash and undrawn facilities",
            ],
            "min_hits": 3,
        },
        # Cash balance for liquidity reconciliation (can also be taken from Section 7)
        "cash_balance": {
            "queries": [
                "cash and cash equivalents closing cash",
                "statement of cash flows closing cash balance",
            ],
            "min_hits": 2,
        },
        # EBITDA for leverage (prefer Section 7; else retrieve)
        "ebitda_reference": {
            "queries": [
                "ebitda adjusted ebitda alternative performance measures",
                "operating profit before depreciation and amortisation",
            ],
            "min_hits": 2,
        },
        # Covenants & security package
        "covenants_and_security": {
            "queries": [
                "financial covenants net leverage interest coverage fixed charge coverage",
                "security package collateral pledge guarantees negative pledge",
                "covenant compliance waiver amendment",
            ],
            "min_hits": 3,
        },
        # Refinancing actions / recent changes
        "refinancing_actions": {
            "queries": [
                "refinancing amend and extend maturity extension",
                "issue of debt bond issuance new facility",
                "repayment of borrowings early redemption",
            ],
            "min_hits": 3,
        },
        # Nearest maturities / upcoming obligations
        "nearest_maturities": {
            "queries": [
                "debt maturity profile next 12 months upcoming maturities",
                "contractual maturities schedule earliest redemption",
            ],
            "min_hits": 2,
        },
        # Liquidity narrative
        "liquidity_discussion": {
            "queries": [
                "liquidity position cash on hand undrawn committed facilities",
                "overdraft capacity accordion option",
                "going concern liquidity and funding resources",
            ],
            "min_hits": 3,
        },
        # Guardrail to exclude internal loans
        "internal_loans_detector": {
            "queries": [
                "shareholder loans related party loans intragroup loans subsidiaries loans",
                "loans from parent undertaking group companies",
            ],
            "min_hits": 1,
        },
    },
    "backoff_rules": {
        "if_section_hits_below": 2,
        "broaden_to": [
            {"drop_adj_keep_nouns": True},
            {"add_alt_terms": {
                "rcf": ["revolving credit facility", "revolver"],
                "coupon": ["interest rate", "margin", "spread"],
                "base_rate": ["euribor", "sofr", "libor", "estr"],
                "bonds": ["notes", "senior notes", "secured notes"],
                "lease liabilities": ["ifrs 16 liabilities", "finance leases"],
                "undrawn": ["headroom", "available facility", "unused commitment"],
                "security": ["collateral", "pledge", "guarantees"],
            }},
        ],
    },
    "format_hints": {
        "part1": "table",                  # facility table for latest year only
        "part2": "bullets",                # commentary bullets
        "table_unit": "millions",
        "table_rounding_dp": 1,
        "maturity_format": "mmm-yy",       # e.g., Jun-25
        "leverage_suffix": "x",
        "na_token": "n.a.",
        "not_meaningful_token": "n.m.",
        "preserve_signs": True,
        "latest_year_only": True,
        "match_financial_highlights": True  # cross-check vs section 7 outputs
    },
    "calculation_rules": {
        "facility_row_capture": {
            "include": [
                "term loan", "tlb", "rcf", "revolving credit facility",
                "bond", "notes", "senior secured notes", "bridge loan",
                "mortgage", "overdraft", "lease liabilities",
            ],
            "exclude_if_contains": [
                "shareholder", "related party", "intragroup", "subsidiaries", "group companies"
            ],
            "fields": {
                "name": "as disclosed (normalize: currency + type + size if stated)",
                "interest_rate": "capture margin/base rate text (e.g., 'EURIBOR + 3.75%')",
                "maturity": "parse to mmm-yy from date strings",
                "amount_outstanding": "numeric; convert to millions; 1 dp",
                "source": "snippet number [#]",
            }
        },
        "summary_rows": [
            {"key": "gross_external_debt", "label": "Gross External Debt", "formula": "sum(amount_outstanding of all included facilities)", "type": "value"},
            {"key": "cash", "label": "Cash", "source": "cash_balance:closing_cash (or financial_highlights.closing_cash)", "type": "value"},
            {"key": "net_external_debt", "label": "Net External Debt", "formula": "gross_external_debt - cash", "type": "value"},
            {"key": "undrawn_total", "label": "Undrawn Facilities", "source": "undrawn_facilities:undrawn_committed_total", "type": "value"},
            {"key": "liquidity", "label": "Liquidity", "formula": "cash + undrawn_total", "type": "value"},
            {"key": "ebitda", "label": "EBITDA", "source": "financial_highlights.ebitda (fallback ebitda_reference)", "type": "value"},
            {"key": "leverage", "label": "Leverage (Net Debt / EBITDA)", "formula": "net_external_debt / ebitda", "type": "ratio", "guard": "if ebitda<=0 or missing → n.m./n.a."},
        ],
        "cross_checks": {
            "prefer_financial_highlights": True,
            "tolerance_percent": 2.0,  # if mismatch vs Section 7 net debt / leverage > 2%, flag and prefer Section 7
        }
    },
    "commentary_topics": [
        "Net debt and leverage trend with underlying factors",
        "Recent refinancing actions and their impact on tenor and pricing",
        "Covenant pressure and status (net leverage, interest coverage, fixed charge coverage)",
        "Security package and collateral (pledges, guarantees, ranking)",
        "Liquidity position (cash on hand, committed undrawn facilities, overdraft capacity, accordion options)",
        "Nearest material maturities and refinancing ability",
    ],
    "normalization_rules": {
        "detect_currency": ["notes headings, statement headers, footers"],
        "detect_scale": ["'Amounts in thousands/millions' indicators"],
        "target_unit": "millions",
        "round_to_dp": 1,
        "apply_scale": "convert reported to millions before aggregation",
        "date_parse_formats": ["YYYY-MM-DD", "DD Month YYYY", "Mon YYYY", "MMM-YY", "Month-YY"],
        "emit_date_format": "mmm-yy",
        "exclude_internal_loans": True,
        "consistent_currency": True
    },
    "extraction_schema": {
        "part1_table": {
            "columns": ["Facility Name", "Interest Rate", "Maturity (mmm-yy)", "Amount Outstanding (m)", "Source #[snippet]"],
            "facility_rows": "dynamic (one per external facility, including lease liabilities)",
            "summary_order": [
                "Gross External Debt",
                "Cash",
                "Net External Debt",
                "Undrawn Facilities",
                "Liquidity",
                "EBITDA",
                "Leverage (Net Debt / EBITDA)"
            ],
        },
        "part2_bullets": {
            "count_range": [6, 10],
            "style": "plain sentences, no semicolons; cite [#] as needed; readable to non-specialists",
        },
    },
}

section9 = """
"""

section10 = """
"""

capital_calculations = """
Capital Structure Table Metrics and Calculations:
 
- The table includes capital structure information for the latest year, using the available annual report/financial statement of the company. It should list out all the debt facilities with the following columns:
-- Name of the Facility (e.g. £300m Term loan, $200m RCF, £100m Senior Secured Notes etc.)
-- Interest Rate (e.g. 5.25%, EURIBOR + 3.75% etc.)
-- Maturity (This is the latest repayment date of the debt facility. It should be provided in the format mmm-yy e.g. Jun-25)
-- Amount Outstanding (Provide it in millions, rounded to 1 decimal point e.g. £1.2m)
- Lease liabilities is also counted as a debt facility (only financial leases, no operational leases). Internal loans such as Shareholder loans, loans from related parties, loans from subsidiaries MUST never be included.
- The table must also contain the following rows:
-- Gross External Debt (Sum of amount outstanding for all debt facilities)
-- Cash (Closing Cash)
-- Net External Debt (Gross Debt – Closing Cash)
-- Liquidity (Closing cash + any undrawn facilities, e.g. undrawn amount of RCF, credit lines or overdrafts). Provide this in millions, rounded to 1 decimal place (e.g. £1.2m)
-- EBITDA
-- Leverage (Net Debt / EBITDA)
- Make sure debt and leverage matches the amount in the financial highlights section
- For the table provide data for the latest year only. All values must be shown in millions, rounded to 1 decimal point (e.g. £1.2m)
"""

finance_calculations = """
Financial Highlights Table Metrics and Calculations:
 
- The table with the following financial information for the last three years, using the last three available annual reports/financial statements of the company. It should have rows (some of which are provided and some of which have to be calculated using provided formulae) including:
-- Revenue (Use Income Statement – Always Given)
-- Gross Profit (Use Income Statement – Always Given): Revenue – Cost of Goods Sold (ONLY use this formula if the report does not already provide the gross profit value)
-- EBITDA (Check all sections of the report, EBITDA or Adjusted EBITDA might be provided – If not provided, calculate manually): Operating Profit + Depreciation and Amortization (ONLY use this formula if the report does not already provide the EBITDA/Adjusted EBITDA value)
-- Revenue Growth % (Always Calculate Manually): (RevenueT0÷RevenueT−1)−1
-- Gross Margin % (Always Calculate Manually): Gross Profit / Revenue
-- EBITDA Margin % (Always Calculate Manually): EBITDA / Revenue (put n.m. if it is negative)
-- Cash Flow from Operating Activities excl. Net Working Capital (Use Cash Flow Statement – Always Calculate Manually): Net Cash Flow from Operating Activities – Net Working Capital (Net Working Capital should be the one calculated below)
-- Net Working Capital (Use Cash Flow Statement – Always Calculate Manually): Increase/Decrease in Debtors/Receivables + Increase/Decrease in Inventory/Stock + Increase/Decrease in Creditors/Payables (These values are usually provided under Cash flows from Operating Activities section of Cash Flow Statement and should be used as it is for calculation (do not change its signs e.g. change from negative to positive))
-- Capex (Use Cash Flow Statement – Always Calculate Manually): Acquisition of Property, Plant, Equipment/Tangible Assets + Acquisition of Intangible Assets (These values are usually provided under Cash flows from Investing Activities section of Cash Flow Statement)
-- Other Cash Flow from Investing Activities (Use Cash Flow Statement – Always Calculate Manually): Net Cash Flow from Investing Activities – Capex (Capex should be the one calculated above)
-- CFADS (Use Cash Flow Statement – Always Calculate Manually): Net Cash Flow from Operating Activities + Net Cash Flow from Investing Activities (Both of these values are always provided in the Cash Flow Statement)
-- Cash Flow from Financing Activities (Use Cash Flow Statement – Always Given): This should include the breakdown of sub-items and their contribution to this net number e.g. debt repayment, debt issuance, share issuance etc.
-- Opening Cash (Use Cash Flow Statement – Always Given)
-- Change in Cash (Use Cash Flow Statement – Always Given)
-- Closing Cash (Use Cash Flow Statement – Always Given)
-- Total Debt (From Debt or Bank Debt or Borrowings or Creditors section – Always Calculate Manually): Bank Debt + Lease Liabilities (This only includes external debt e.g. bank loans, bonds, RCFs etc. and lease liabilities (only financial leases, not operating leases), and no internal debt (e.g. shareholder loans, loans from related parties, loans from subsidiaries etc.)) 
-- Net Debt (Always Calculate Manually): Net Debt: Total Debt – Closing Cash
-- Leverage (Always Calculate Manually): Net Debt / EBITDA (put n.m. if it is negative)
- For the table, provide data from the last three fiscal years (e.g. FY22, FY23, FY24). All values must be shown in millions, rounded to 1 decimal point (e.g. £1.2m). Leverage must be reported in the following format e.g. 1.2x. Show the values as they are reported and calculated e.g. If capex is in negative, it should be reported in negative in the table.
"""

