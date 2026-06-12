# Power BI Dashboard Build Guide
## Bluestock MF Analytics — 4-Page Dashboard

---

## Prerequisites

- Power BI Desktop (free, download from microsoft.com/power-bi)
- All CSVs in `data/processed/`
- Files in this `dashboard/` folder

---

## Step 1 — Load Data (M Queries)

1. Open Power BI Desktop → **Get Data → Blank Query**
2. Open **Advanced Editor** (Home tab)
3. For each table, paste the corresponding block from `powerbi_m_queries.txt`
4. **Change** `D:\MutualFundAnalytics\` to your actual folder path in every query
5. Create all 8 queries with these exact names:

| Query Name | Source File |
|---|---|
| `dim_Fund` | 01_fund_master_cleaned.csv |
| `fact_NAV` | 02_nav_history_cleaned.csv |
| `fact_AUM` | 03_aum_by_fund_house_cleaned.csv |
| `fact_SIPInflows` | 04_monthly_sip_inflows_cleaned.csv |
| `fact_Performance` | 07_scheme_performance_cleaned.csv |
| `fact_Transactions` | 08_investor_transactions_cleaned.csv |
| `fact_Scorecard` | fund_scorecard.csv |
| `fact_AlphaBeta` | alpha_beta.csv |

6. Click **Close & Apply**

---

## Step 2 — Create Relationships (Model View)

Click the **Model** icon (left sidebar). Create these relationships:

| From Table → Column | To Table → Column | Cardinality |
|---|---|---|
| `fact_NAV[amfi_code]` | `dim_Fund[amfi_code]` | Many-to-One ★ |
| `fact_Performance[amfi_code]` | `dim_Fund[amfi_code]` | Many-to-One |
| `fact_Transactions[amfi_code]` | `dim_Fund[amfi_code]` | Many-to-One |
| `fact_Scorecard[amfi_code]` | `dim_Fund[amfi_code]` | Many-to-One |
| `fact_AlphaBeta[amfi_code]` | `dim_Fund[amfi_code]` | Many-to-One |
| `fact_AUM[fund_house]` | `dim_Fund[fund_house]` | Many-to-Many (set cross-filter: Both) |

> ★ Set `fact_NAV` → `dim_Fund` as the **active** relationship.

---

## Step 3 — Apply Theme

1. Go to **View** tab → **Themes** → **Browse for themes**
2. Select `dashboard/bluestock_theme.json`

---

## Step 4 — Add DAX Measures

1. Go to **Home → New Table**, type: `Measures = {}`  → creates a blank table
2. Select the `Measures` table in the Fields pane
3. **Home → New Measure** — paste each measure from `dax_measures.txt` one by one

---

## Step 5 — Build Page 1: Industry Overview

**Canvas size:** 1280 × 720 (16:9). Set in View → Page View → Actual Size.

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  BLUESTOCK MF ANALYTICS          [logo placeholder]         │
│  Industry Overview Dashboard                                 │
├──────────┬──────────┬──────────┬──────────────────────────  │
│ KPI Card │ KPI Card │ KPI Card │ KPI Card                   │
│ Total AUM│ SIP Inflow│ Folios  │ SIP YoY Growth             │
├──────────┴──────────┴──────────┴──────────┬─────────────────┤
│                                            │                 │
│    Industry AUM Trend Line Chart           │  AUM by AMC     │
│    (2022-2025, by date)                    │  Bar Chart      │
│                                            │  (horizontal)   │
└────────────────────────────────────────────┴─────────────────┘
```

### Visuals

**4 KPI Cards** (Insert → Card visual):
1. Card → Field: `[Total AUM (Lakh Cr)]` → Label: "Total AUM (₹ Lakh Cr)"
2. Card → Field: `[Latest SIP Inflow (Cr)]` → Label: "Monthly SIP (₹ Cr)"
3. Card → Field: `[Total Folios (Cr)]` → Label: "Total Folios (Cr)"
4. Card → Field: `[SIP YoY Growth %]` → Label: "SIP YoY Growth"

**Industry AUM Trend Line Chart**:
- Visual: Line Chart
- X-axis: `fact_AUM[date]` (set to Month hierarchy)
- Y-axis: `[AUM Lakh Crore]`
- Legend: None (industry total)
- Title: "Industry AUM Trend (₹ Lakh Crore)"
- Format: Line color #1565C0, stroke 2.5px

**AUM by AMC Bar Chart**:
- Visual: Clustered Bar Chart
- Y-axis: `fact_AUM[fund_house]`
- X-axis: `[AUM Lakh Crore]`
- Sort: Descending by value
- Data labels: On
- Color: #1565C0, highlight SBI with #E53935 using conditional formatting
- Title: "AUM by Fund House (₹ Lakh Cr)"

**Text box** at top: "Bluestock MF Analytics — Industry Overview"
Font: Segoe UI, 18pt, Bold, color #1565C0

---

## Step 6 — Build Page 2: Fund Performance

Right-click page tab → **Add Page** → rename "Fund Performance"

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Slicers: [Fund House ▼] [Category ▼] [Plan ▼]             │
├───────────────────────────┬─────────────────────────────────┤
│                           │                                 │
│  Scatter Plot             │   NAV Line vs Benchmark         │
│  X=Return, Y=StdDev       │   (filtered by slicer)          │
│  Bubble=AUM               │                                 │
├───────────────────────────┴─────────────────────────────────┤
│                                                             │
│   Fund Scorecard Table (sortable)                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Visuals

**Slicers** (Insert → Slicer):
1. Field: `dim_Fund[fund_house]` → Style: Dropdown
2. Field: `dim_Fund[category]` → Style: Dropdown
3. Field: `dim_Fund[plan]` → Style: Tile

**Scatter Plot** (Insert → Scatter Chart):
- X-axis: `fact_Performance[return_3yr_pct]`
- Y-axis: `fact_Performance[std_dev_ann_pct]`
- Size: `fact_Performance[aum_crore]`
- Legend: `fact_Performance[category]`
- Details: `fact_Performance[scheme_name]`
- Title: "Return vs Risk (3yr CAGR vs StdDev)"
- Tooltip: Add `[sharpe_ratio]`, `[expense_ratio_pct]`
- Format: Legend on Right, bubble max size 30

**NAV Line Chart**:
- Visual: Line Chart
- X-axis: `fact_NAV[date]`
- Y-axis: `fact_NAV[nav]`
- Legend: `dim_Fund[scheme_name]`
- Title: "NAV Trend — Selected Fund(s)"
- Filter: This visual only shows when 1 fund is selected via slicer

**Fund Scorecard Table**:
- Visual: Table
- Columns (in order):
  1. `fact_Scorecard[overall_rank]` → rename "Rank"
  2. `fact_Scorecard[scheme_name]` → rename "Fund Name"
  3. `fact_Scorecard[composite_score]` → rename "Score"
  4. `fact_Scorecard[cagr_3yr_pct]` → rename "3yr CAGR%"
  5. `fact_Scorecard[sharpe_ratio_calc]` → rename "Sharpe"
  6. `fact_Scorecard[alpha_annualised]` → rename "Alpha%"
  7. `fact_Scorecard[max_dd_pct]` → rename "Max DD%"
  8. `fact_Scorecard[expense_ratio_pct]` → rename "TER%"
- Sort: By Rank ascending
- Conditional formatting on "Score": Data bar, color #1565C0
- Conditional formatting on "3yr CAGR%": Background, Green-White-Red scale

**Drill-through setup**:
1. Right-click "Fund Performance" page → Add drill-through
2. Create a new page named "NAV Detail"
3. On NAV Detail page, add `dim_Fund[scheme_name]` to the drill-through field well
4. Add a large NAV line chart, scorecard metrics, and alpha/beta table
5. Back on Fund Performance, right-click any fund row → Drill through → NAV Detail

---

## Step 7 — Build Page 3: Investor Analytics

Right-click page tab → **Add Page** → rename "Investor Analytics"

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Slicers: [State ▼] [Age Group ▼] [City Tier ▼]            │
├──────────────────┬──────────────────┬───────────────────────┤
│ Bar Chart        │ Donut Chart      │ Bar Chart             │
│ Amount by State  │ SIP/Lumpsum/Rdm  │ Age Group vs Avg SIP  │
│ (top 12)         │ split            │ amount                │
├──────────────────┴──────────────────┴───────────────────────┤
│                                                             │
│   Monthly Transaction Volume Line Chart                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Visuals

**Slicers**:
1. Field: `fact_Transactions[state]` → Style: Dropdown
2. Field: `fact_Transactions[age_group]` → Style: Tile
3. Field: `fact_Transactions[city_tier]` → Style: Tile

**Bar Chart — Amount by State**:
- Visual: Clustered Bar Chart
- Y-axis: `fact_Transactions[state]`
- X-axis: `[Total Amount (Cr)]`
- Top N filter: Top 12 by `[Total Amount (Cr)]`
- Sort: Descending
- Title: "SIP Investment by State (₹ Cr)"
- Tooltip: Add `[SIP Count]`, `[Transaction Count]`

**Donut Chart — Transaction Type Split**:
- Visual: Donut Chart
- Legend: `fact_Transactions[transaction_type]`
- Values: `[Total Amount (Cr)]`
- Title: "Transaction Mix (₹ Cr)"
- Colors: SIP=#1565C0, Lumpsum=#43A047, Redemption=#E53935

**Bar Chart — Age Group vs Avg SIP**:
- Visual: Clustered Column Chart
- X-axis: `fact_Transactions[age_group]`
- Y-axis: `[Avg SIP Amount]`
- Sort by: Age Group (custom order: 18-25, 26-35, 36-45, 46-55, 56+)
  → Column Tools → Sort by Column → create Index column in M if needed
- Title: "Avg SIP Amount by Age Group (₹)"

**Monthly Transaction Volume Line**:
- Visual: Line Chart
- X-axis: `fact_Transactions[Month]`
- Y-axis: `[Total Amount (Cr)]`
- Line color: #1565C0
- Title: "Monthly Transaction Volume (₹ Cr)"
- Enable: Markers on data points

---

## Step 8 — Build Page 4: SIP & Market Trends

Right-click page tab → **Add Page** → rename "SIP & Market Trends"

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Dual-Axis: SIP Inflow (Bar) + Nifty 50 Index (Line)      │
│   2022–2025                                                 │
│                                                             │
├──────────────────────────────┬──────────────────────────────┤
│                              │                              │
│   Category Inflow Heatmap    │   Top 5 Categories FY25      │
│   (Matrix visual)            │   Bar Chart                  │
│                              │                              │
└──────────────────────────────┴──────────────────────────────┘
```

### Visuals

**Dual-Axis Chart** (SIP + Nifty 50):

Since Power BI doesn't natively dual-axis two different tables, use a Line and Clustered Column Chart:

Step 1 — Load Nifty 50 data as a separate query:
```
// Add this M query as "fact_Benchmark"
let
    Source = Csv.Document(
        File.Contents("D:\MutualFundAnalytics\data\raw\10_benchmark_indices.csv"),
        [Delimiter=",", Columns=3, Encoding=65001]
    ),
    Headers = Table.PromoteHeaders(Source),
    Typed = Table.TransformColumnTypes(Headers, {
        {"date", type date}, {"index_name", type text}, {"close_value", type number}
    }),
    Nifty50 = Table.SelectRows(Typed, each [index_name] = "NIFTY50"),
    AddMonth = Table.AddColumn(Nifty50, "Month", each Date.ToText([date], "yyyy-MM"))
in
    AddMonth
```

Step 2 — Build dual-axis visual:
- Visual: Line and Clustered Column Chart
- Shared axis: Month (align fact_SIPInflows[month] and fact_Benchmark[Month])
  → Create a Date table or use text month key
- Column values: `[SIP Inflow (Cr)]` from fact_SIPInflows
- Line values: `AVERAGE(fact_Benchmark[close_value])` where index=NIFTY50
- Column Y-axis title: "SIP Inflow (₹ Cr)"
- Line Y-axis title: "Nifty 50 Index"
- Title: "SIP Inflow vs Nifty 50 (2022–2025)"

**Category Inflow Heatmap** (Matrix visual):

Load category inflows:
```
// Add M query as "fact_CategoryInflows"
let
    Source = Csv.Document(
        File.Contents("D:\MutualFundAnalytics\data\raw\05_category_inflows.csv"),
        [Delimiter=",", Columns=3, Encoding=65001]
    ),
    Headers = Table.PromoteHeaders(Source),
    Typed = Table.TransformColumnTypes(Headers, {
        {"month", type date}, {"category", type text}, {"net_inflow_crore", type number}
    }),
    AddMonthStr = Table.AddColumn(Typed, "MonthStr", each Date.ToText([month], "yyyy-MM"))
in
    AddMonthStr
```

Matrix visual setup:
- Visual: Matrix
- Rows: `fact_CategoryInflows[category]`
- Columns: `fact_CategoryInflows[MonthStr]`
- Values: `SUM(fact_CategoryInflows[net_inflow_crore])`
- Conditional formatting on Values:
  → Background color → Rules: Lowest=white, Highest=#E53935
  → This creates the heatmap effect
- Title: "Category Net Inflows Heatmap (₹ Cr)"

**Top 5 Categories FY25 Bar Chart**:
- Filter: MonthStr >= "2024-04" AND <= "2025-03"
- Visual: Clustered Bar Chart
- Y-axis: `fact_CategoryInflows[category]`
- X-axis: `SUM(fact_CategoryInflows[net_inflow_crore])`
- Top N: 5
- Sort: Descending
- Title: "Top 5 Categories by Net Inflow FY25 (₹ Cr)"
- Data labels: On, color white

---

## Step 9 — Add Interactivity & Tooltips

### Drill-through (already set up in Step 6)
- On Fund Performance page table, right-click any row → Drill through → NAV Detail

### Cross-filter all pages
- Format → Edit Interactions → set all visuals to "Filter" mode (not "Highlight")

### Tooltips on charts
For each visual, go to **Format → Tooltip**:
- Add relevant fields in the Tooltip Fields well
- Scatter: scheme_name, sharpe_ratio, alpha, expense_ratio_pct
- AUM Bar: aum_crore, num_schemes, fund_house
- Transaction Bar: state, transaction_count, avg_amount
- NAV Line: date, nav, is_trading_day

### Page navigation buttons
1. Insert → Buttons → Blank
2. Set Action → Type: Page Navigation → Destination: target page
3. Style: fill #1565C0, text white
4. Create one on each page: "← Back" and "Next →"

---

## Step 10 — Apply Bluestock Branding

### Logo placeholder
1. Insert → Image → select any placeholder or your logo PNG
2. Position top-left of each page, size 120×40px

### Header text box on each page
- Insert → Text Box
- Text: "BLUESTOCK MF ANALYTICS" + page title
- Font: Segoe UI Semibold, 16pt, color #1565C0
- Background: white or very light grey (#F5F7FA)

### Consistent styling checklist
- All chart backgrounds: white (#FFFFFF)
- All chart titles: Segoe UI, 12pt, Bold, #1565C0
- All axis labels: Segoe UI, 10pt, #546E7A
- Grid lines: light grey, 1px
- Card values: Segoe UI, 28pt, Bold, #1565C0
- Card labels: Segoe UI, 10pt, #546E7A

---

## Step 11 — Export

### Save as .pbix
- File → Save As → bluestock_mf_dashboard.pbix
- Save to: `D:\MutualFundAnalytics\dashboard\`

### Export to PDF
- File → Export → Export to PDF
- Save as: `dashboard/Dashboard.pdf`

### Export pages as PNG
- For each page (4 pages):
  1. File → Export → Export to PowerPoint (exports each slide)
  OR
  2. Use Print → Microsoft Print to PDF → save each page
  OR (best method):
  3. File → Export → Export to PDF → then use any PDF-to-PNG tool
  4. Name files: `Page1_Industry_Overview.png`, `Page2_Fund_Performance.png`,
     `Page3_Investor_Analytics.png`, `Page4_SIP_Market_Trends.png`
- Save all PNGs to: `dashboard/screenshots/`

---

## Relationship Diagram Summary

```
dim_Fund (amfi_code) ──┬──< fact_NAV (amfi_code)
                       ├──< fact_Performance (amfi_code)
                       ├──< fact_Transactions (amfi_code)
                       ├──< fact_Scorecard (amfi_code)
                       └──< fact_AlphaBeta (amfi_code)

dim_Fund (fund_house) ──< fact_AUM (fund_house)

fact_SIPInflows     — standalone (no relationship needed)
fact_CategoryInflows — standalone
fact_Benchmark      — standalone
```

---

## Quick Reference: KPI Target Values

| KPI | Target Value | Source |
|---|---|---|
| Total AUM | ~₹81 Lakh Crore | fact_AUM latest snapshot |
| SIP Inflow | ₹31,002 Cr | fact_SIPInflows Dec 2025 |
| Total Folios | 26.12 Cr | Static / fact_FolioCount |
| Total Schemes | 40 (our dataset) / 1,908 (industry) | dim_Fund count |
| SIP YoY Growth | ~17% | fact_SIPInflows |

---

## Troubleshooting

| Issue | Fix |
|---|---|
| "Cannot find file" error | Update path in M query to match your actual folder |
| Relationship ambiguity warning | Set active relationship in Model view |
| Date hierarchy not showing | Right-click date column → Mark as Date Table |
| Scatter plot too crowded | Add a Top N filter: Top 20 by AUM |
| Heatmap colors not working | Conditional formatting must be set on measure, not column |
| Dual axis not aligning | Create a shared Date dimension table |
