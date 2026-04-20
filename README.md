#  DCF Valuation Model

An interactive Discounted Cash Flow (DCF) valuation tool that estimates the intrinsic value per share of a company. Built with Python and Streamlit, featuring dual discount-rate modes (direct input or full WACC/CAPM calculation), projected free cash flow visualisations, an enterprise-value waterfall chart, and a two-dimensional sensitivity analysis heatmap.

---

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/Miguel-B-A/DCF-ValuationModel
cd DCF-Valuation
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

The project depends on:

| Package | Purpose |
|---------|---------|
| `numpy` | Array operations and numerical computation |
| `pandas` | DataFrames for tabular display |
| `streamlit` | Interactive web UI |
| `plotly` | Bar charts, waterfall diagram, and heatmap |

3. **Run the application**

```bash
streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## Project Structure

```
DCF-Valuation/
├── dcf_model.py        # Core DCF class — all valuation logic
├── streamlit_app.py    # Streamlit UI layer
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

**`dcf_model.py`** contains a single `DCF` class with methods that mirror the valuation chain described below. Every calculation is isolated in its own method so each step can be inspected, tested, or extended independently.

**`streamlit_app.py`** handles user input, instantiates the model, and renders results. It never performs financial calculations directly — all math lives in `dcf_model.py`.

---

## How to Use the App

1. **Choose a discount-rate mode** in the sidebar:
   - **Direct** — enter a single discount rate manually (e.g. 10%).
   - **WACC (CAPM)** — supply risk-free rate, beta, equity risk premium, cost of debt, tax rate, market cap, and total debt. The app computes cost of equity via CAPM and blends it into WACC automatically.

2. **Set FCF assumptions** — latest free cash flow, growth rate, terminal growth rate, and projection horizon.

3. **Enter equity bridge inputs** — cash & equivalents, total debt, and shares outstanding.

4. **Read the results** — KPI cards show the discount rate, enterprise value, equity value, and implied price per share. Below, you'll find a projected FCF bar chart, an enterprise-value waterfall, a sensitivity heatmap, and a raw data table.

---

## Theory — What Is a DCF?

### The Core Idea

A Discounted Cash Flow analysis answers a simple question: **what is a company worth today, given the cash it is expected to generate in the future?**

Money received in the future is worth less than money received today for two reasons: you could invest today's money and earn a return (opportunity cost), and there is uncertainty about whether future cash flows will actually materialise (risk). A DCF formalises this by projecting future cash flows and discounting them back to the present at a rate that reflects both the time value of money and the specific risk of the investment.

### Step 1 — Free Cash Flow (FCF)

Free cash flow is the cash a company produces from its operations after paying for capital expenditures needed to maintain and grow the business:

```
FCF = Operating Cash Flow − Capital Expenditures
```

This is the cash that is truly "free" — available to pay debt holders, return to shareholders, or reinvest. It is the foundation of a DCF because it measures actual cash generation rather than accounting profit.

To project future FCFs, we take the most recent FCF and grow it at an assumed annual rate:

```
FCF_t = FCF_0 × (1 + g)^t     for t = 1, 2, ..., n
```

where `g` is the growth rate and `n` is the number of projection years. The growth rate is a judgment call — it can be informed by historical growth, analyst consensus, or industry benchmarks.

### Step 2 — Terminal Value (Gordon Growth Model)

We cannot project cash flows year by year to infinity. Instead, at the end of the projection period, we estimate a **terminal value** that captures all cash flows from year n+1 onward. The Gordon Growth Model assumes a constant perpetual growth rate `g_t`:

```
TV = FCF_n × (1 + g_t) / (r − g_t)
```

where `r` is the discount rate and `g_t` is the terminal growth rate. A key constraint is that `r > g_t`; otherwise the formula produces infinite or negative values, which is economically nonsensical (it would imply the company grows faster than the economy forever).

Terminal growth is typically set at 2–3 %, roughly in line with long-run GDP growth or inflation. Terminal value often accounts for 60–80 % of total enterprise value, which is why this assumption has such an outsized impact on the final result.

### Step 3 — Discount Rate

The discount rate converts future cash flows into present value. It represents the minimum return investors require given the riskiness of the company. This model supports two ways of determining it:

#### Option A — Direct Input

Simply provide a rate based on the type of company (e.g. 8–10 % for large stable firms, 12–15 % for high-risk ventures).

#### Option B — WACC (Weighted Average Cost of Capital)

WACC blends the cost of equity and the after-tax cost of debt, weighted by the company's capital structure:

```
WACC = (E / V) × Re + (D / V) × Rd × (1 − t)
```

| Symbol | Meaning |
|--------|---------|
| E | Market capitalisation (equity) |
| D | Total debt |
| V | E + D (total firm value) |
| Re | Cost of equity |
| Rd | Pre-tax cost of debt |
| t | Corporate tax rate |

Debt gets the `(1 − t)` adjustment because interest payments are tax-deductible, making the effective cost of debt lower than its stated rate.

**Cost of Equity (CAPM)**

The Capital Asset Pricing Model estimates the return equity investors require:

```
Re = Rf + β × ERP
```

| Symbol | Meaning |
|--------|---------|
| Rf | Risk-free rate (e.g. 10-year Treasury yield) |
| β | Beta — sensitivity of the stock to market movements |
| ERP | Equity risk premium — extra return demanded for holding equities over risk-free assets |

Beta of 1.0 means the stock moves with the market; above 1.0 means more volatile. The equity risk premium is historically around 5–7 % for the US market but is an ongoing area of debate among academics and practitioners.

### Step 4 — Enterprise Value

Discount every projected FCF and the terminal value back to today, then sum them:

```
EV = Σ [ FCF_t / (1 + r)^t ] + TV / (1 + r)^n
```

This gives the total present value of the firm's operations — the **enterprise value**.

### Step 5 — Equity Value and Price per Share

Enterprise value belongs to all capital providers (debt + equity). To isolate the value attributable to shareholders:

```
Equity Value = Enterprise Value − Total Debt + Cash & Equivalents
```

Cash is added back because it is a liquid asset owned by shareholders. Dividing by shares outstanding yields the **implied price per share**:

```
Price per Share = Equity Value / Shares Outstanding
```

Compare this to the current market price: if the implied price is higher, the stock may be undervalued under your assumptions; if lower, it may be overvalued.

### Step 6 — Sensitivity Analysis

Every DCF depends on assumptions — most critically, the growth rate and the discount rate. Small changes in either can swing the result significantly. Rather than presenting a single-point estimate, a sensitivity analysis builds a grid of implied prices across a range of growth and discount rate combinations. This honestly communicates the range of possible outcomes and lets the user judge how robust the valuation is.

---

## Limitations

- **Constant growth assumption**: the model projects FCFs at a single constant growth rate. Real companies experience varying growth across different stages.
- **Terminal value dominance**: because terminal value often represents the majority of enterprise value, the result is highly sensitive to terminal growth rate and discount rate assumptions.
- **No multi-stage growth**: a more sophisticated model might use higher growth for the first few years, tapering to a mature growth rate before applying the terminal value.
- **Judgment-dependent inputs**: the equity risk premium, growth rate, and terminal growth rate are all subjective. The model provides the framework, but the quality of the output depends on the quality of the assumptions.

---

## License

This project is for educational and portfolio demonstration purposes.
