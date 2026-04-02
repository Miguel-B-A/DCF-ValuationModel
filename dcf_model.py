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

        TODO
        ----
        - Use self.risk_free_rate, self.beta, self.equity_risk_premium
        - Raise ValueError if any required inputs are None
        """
        pass

    def wacc(self) -> float:
        """
        Weighted Average Cost of Capital.

        WACC = (E/V) × Re + (D/V) × Rd × (1 - t)

        where V = E + D (total firm value = equity + debt)

        Returns
        -------
        float
            Blended discount rate reflecting capital structure.

        TODO
        ----
        - Compute equity weight: E / (E + D) using market_cap and total_debt
        - Compute debt weight: D / (E + D)
        - After-tax cost of debt: cost_of_debt × (1 - tax_rate)
        - Combine with cost_of_equity()
        - Raise ValueError if required WACC inputs are None
        """
        pass

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
        pass

    def free_cash_flows(self) -> np.ndarray:
        """
        Project future free cash flows for each year in the projection period.

        FCF_t = latest_fcf × (1 + growth_rate)^t   for t = 1, ..., projection_years

        Returns
        -------
        np.ndarray
            Array of projected FCFs, length = projection_years.

        TODO
        ----
        - Build array of projected FCFs using compound growth
        - Consider: should growth be constant, or could you extend this
          to accept a list of year-by-year growth rates later?
        """
        pass

    def terminal_value(self) -> float:
        """
        Gordon Growth Model terminal value at the end of the projection period.

        TV = FCF_n × (1 + g) / (r - g)

        where FCF_n is the last projected FCF, g is terminal_growth_rate,
        and r is the discount rate.

        Returns
        -------
        float
            Terminal value (undiscounted — still at year n).

        TODO
        ----
        - Get last projected FCF from free_cash_flows()
        - Apply Gordon Growth formula
        - Validate that discount_rate > terminal_growth_rate
        """
        pass

    def enterprise_value(self) -> float:
        """
        Sum of all discounted FCFs plus discounted terminal value.

        EV = Σ [FCF_t / (1 + r)^t] + TV / (1 + r)^n

        Returns
        -------
        float
            Present value of the entire firm's operations.

        TODO
        ----
        - Discount each projected FCF back to present
        - Discount terminal value back to present
        - Sum everything
        """
        pass

    def equity_value(self) -> float:
        """
        Equity Value = Enterprise Value - Net Debt

        where Net Debt = Total Debt - Cash & Equivalents

        Returns
        -------
        float
            Value attributable to equity holders.

        TODO
        ----
        - Compute net debt
        - Subtract from enterprise_value()
        - Think about: what if equity value is negative? What does that mean?
        """
        pass

    def price_per_share(self) -> float:
        """
        Implied share price = Equity Value / Shares Outstanding

        Returns
        -------
        float
            Intrinsic value per share.

        TODO
        ----
        - Divide equity_value() by shares_outstanding
        - Raise ValueError if shares_outstanding is None or <= 0
        """
        pass

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

        TODO
        ----
        - Create default ranges if not provided
        - For each (g, r) pair, temporarily override self.growth_rate and
          self.discount_rate, compute price_per_share(), then restore originals
        - Watch out for the mutation bug we hit in the Bond Pricer!
          Consider creating a fresh DCF instance for each combo instead
          of mutating self, or save/restore state carefully.
        """
        pass
