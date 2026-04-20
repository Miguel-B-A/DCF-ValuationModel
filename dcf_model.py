import numpy as np


class DCF:
    """
    Discounted Cash Flow valuation model.

    Takes a company's financial data and assumptions to estimate
    intrinsic value per share via DCF analysis.
    """

    def __init__(
        self,
        latest_fcf: float,
        growth_rate: float,
        terminal_growth_rate: float,
        discount_rate: float = None,  # If provided directly, skip WACC calc
        projection_years: int = 5,
        # WACC components (used if discount_rate is None)
        risk_free_rate: float = None,
        beta: float = None,
        equity_risk_premium: float = None,
        cost_of_debt: float = None,
        tax_rate: float = None,
        market_cap: float = None,
        total_debt: float = None,
        # Equity bridge
        cash_and_equivalents: float = 0.0,
        shares_outstanding: float = None,
    ):
        """
        Parameters
        ----------
        latest_fcf : float
            Most recent trailing twelve-month free cash flow.
        growth_rate : float
            Assumed annual FCF growth rate during projection period (e.g. 0.08 for 8%).
        terminal_growth_rate : float
            Perpetual growth rate for terminal value (e.g. 0.025 for 2.5%).
        discount_rate : float, optional
            If provided, used directly as the discount rate (bypasses WACC calculation).
        projection_years : int
            Number of years to project FCFs (default 5).
        risk_free_rate : float, optional
            Yield on risk-free asset (e.g. 10-year Treasury). Used in WACC/CAPM.
        beta : float, optional
            Stock's beta relative to the market. Used in CAPM.
        equity_risk_premium : float, optional
            Expected market return minus risk-free rate. Used in CAPM.
        cost_of_debt : float, optional
            Pre-tax cost of debt. Used in WACC.
        tax_rate : float, optional
            Corporate tax rate. Used to compute after-tax cost of debt.
        market_cap : float, optional
            Market capitalisation (equity weight in WACC).
        total_debt : float, optional
            Total debt outstanding (debt weight in WACC).
        cash_and_equivalents : float
            Cash & short-term investments (subtracted to get net debt).
        shares_outstanding : float, optional
            Diluted shares outstanding for per-share calculation.
        """
        self.latest_fcf = latest_fcf
        self.growth_rate = growth_rate
        self.terminal_growth_rate = terminal_growth_rate
        self.discount_rate = discount_rate
        self.projection_years = projection_years

        # WACC / CAPM inputs
        self.risk_free_rate = risk_free_rate
        self.beta = beta
        self.equity_risk_premium = equity_risk_premium
        self.cost_of_debt = cost_of_debt
        self.tax_rate = tax_rate
        self.market_cap = market_cap
        self.total_debt = total_debt

        # Equity bridge inputs
        self.cash_and_equivalents = cash_and_equivalents
        self.shares_outstanding = shares_outstanding

    # Core valuation methods 

    def cost_of_equity(self) -> float:
        """
        CAPM: Cost of Equity = Rf + β × ERP

        Returns
        -------
        float
            Required return on equity.
        """
        if any(v is None for v in (self.risk_free_rate, self.beta, self.equity_risk_premium)):
            raise ValueError(
                "risk_free_rate, beta, and equity_risk_premium are required for CAPM."
            )
        return self.risk_free_rate + self.beta * self.equity_risk_premium

    def wacc(self) -> float:
        """
        Weighted Average Cost of Capital.

        WACC = (E/V) × Re + (D/V) × Rd × (1 - t)

        where V = E + D (total firm value = equity + debt)

        Returns
        -------
        float
            Blended discount rate reflecting capital structure.
        """
        if any(v is None for v in (self.cost_of_debt, self.tax_rate, self.market_cap, self.total_debt)):
            raise ValueError(
                "cost_of_debt, tax_rate, market_cap, and total_debt are required for WACC."
            )
        E = self.market_cap
        D = self.total_debt
        V = E + D
        re = self.cost_of_equity()
        rd_after_tax = self.cost_of_debt * (1 - self.tax_rate)
        return (E / V) * re + (D / V) * rd_after_tax

    def get_discount_rate(self) -> float:
        """
        Return the discount rate to use in the valuation.

        If self.discount_rate was provided directly, return it.
        Otherwise, compute and return WACC.

        Returns
        -------
        float
            The discount rate for DCF calculations.
        """
        if self.discount_rate is not None:
            return self.discount_rate
        return self.wacc()

    def free_cash_flows(self) -> np.ndarray:
        """
        Project future free cash flows for each year in the projection period.

        FCF_t = latest_fcf × (1 + growth_rate)^t   for t = 1, ..., projection_years

        Returns
        -------
        np.ndarray
            Array of projected FCFs, length = projection_years.
        """
        t = np.arange(1, self.projection_years + 1)
        return self.latest_fcf * (1 + self.growth_rate) ** t

    def terminal_value(self, fcf_n: float = None) -> float:
        """
        Gordon Growth Model terminal value at the end of the projection period.

        TV = FCF_n × (1 + g) / (r - g)

        where FCF_n is the last projected FCF, g is terminal_growth_rate,
        and r is the discount rate.

        Parameters
        ----------
        fcf_n : float, optional
            Last projected FCF. Computed from free_cash_flows() if not supplied.

        Returns
        -------
        float
            Terminal value (undiscounted — still at year n).
        """
        r = self.get_discount_rate()
        g = self.terminal_growth_rate
        if r <= g:
            raise ValueError(
                f"discount_rate ({r:.4f}) must exceed terminal_growth_rate ({g:.4f})."
            )
        if fcf_n is None:
            fcf_n = self.free_cash_flows()[-1]
        return fcf_n * (1 + g) / (r - g)

    def enterprise_value(self) -> float:
        """
        Sum of all discounted FCFs plus discounted terminal value.

        EV = Σ [FCF_t / (1 + r)^t] + TV / (1 + r)^n

        Returns
        -------
        float
            Present value of the entire firm's operations.
        """
        r = self.get_discount_rate()
        n = self.projection_years
        t = np.arange(1, n + 1)
        fcfs = self.free_cash_flows()
        pv_fcfs = np.sum(fcfs / (1 + r) ** t)
        pv_tv = self.terminal_value(fcf_n=fcfs[-1]) / (1 + r) ** n
        return pv_fcfs + pv_tv

    def equity_value(self) -> float:
        """
        Equity Value = Enterprise Value - Net Debt

        where Net Debt = Total Debt - Cash & Equivalents

        Returns
        -------
        float
            Value attributable to equity holders.
        """
        net_debt = (self.total_debt or 0.0) - self.cash_and_equivalents
        return self.enterprise_value() - net_debt

    def price_per_share(self) -> float:
        """
        Implied share price = Equity Value / Shares Outstanding

        Returns
        -------
        float
            Intrinsic value per share.
        """
        if not self.shares_outstanding or self.shares_outstanding <= 0:
            raise ValueError("shares_outstanding must be a positive number.")
        return self.equity_value() / self.shares_outstanding

    def sensitivity_analysis(
        self,
        growth_rates: np.ndarray = None,
        discount_rates: np.ndarray = None,
    ) -> np.ndarray:
        """
        Build a 2D grid of implied share prices across
        different growth rate and discount rate assumptions.

        Parameters
        ----------
        growth_rates : np.ndarray, optional
            Array of growth rates to test. Defaults to ±2% around self.growth_rate.
        discount_rates : np.ndarray, optional
            Array of discount rates to test. Defaults to ±2% around get_discount_rate().

        Returns
        -------
        np.ndarray
            2D array of shape (len(discount_rates), len(growth_rates))
            containing implied price per share for each combination.
        """
        base_r = self.get_discount_rate()
        if growth_rates is None:
            growth_rates = np.linspace(self.growth_rate - 0.02, self.growth_rate + 0.02, 5)
        if discount_rates is None:
            discount_rates = np.linspace(base_r - 0.02, base_r + 0.02, 5)

        grid = np.empty((len(discount_rates), len(growth_rates)))
        for i, r in enumerate(discount_rates):
            for j, g in enumerate(growth_rates):
                scenario = DCF(
                    latest_fcf=self.latest_fcf,
                    growth_rate=g,
                    terminal_growth_rate=self.terminal_growth_rate,
                    discount_rate=r,
                    projection_years=self.projection_years,
                    cash_and_equivalents=self.cash_and_equivalents,
                    total_debt=self.total_debt,
                    shares_outstanding=self.shares_outstanding,
                )
                grid[i, j] = scenario.price_per_share()
        return grid
