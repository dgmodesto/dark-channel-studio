from decimal import Decimal


class ProviderError(Exception):
    """Base error: stable `code` plus `params`, never localized text or secrets."""

    code = "provider.error"

    def __init__(self, message: str = "", **params: object):
        self.params = params
        super().__init__(message or self.code)


class ProviderConfigError(ProviderError):
    code = "provider.config_invalid"

    def __init__(self, code: str, message: str, **params: object):
        self.code = code
        super().__init__(message, **params)


class ProviderCallError(ProviderError):
    code = "provider.call_failed"


class BudgetExceededError(ProviderError):
    code = "budget.exceeded"

    def __init__(self, run_id: str, cap_usd: Decimal, spent_usd: Decimal):
        super().__init__(
            f"budget exceeded for run {run_id}",
            run_id=run_id,
            cap_usd=str(cap_usd),
            spent_usd=str(spent_usd),
        )
