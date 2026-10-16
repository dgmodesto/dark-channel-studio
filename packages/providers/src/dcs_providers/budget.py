from dataclasses import dataclass, field
from decimal import Decimal

from dcs_providers.errors import BudgetExceededError


@dataclass
class RunBudget:
    """Per-run spend cap. Calls are blocked once spend has reached the cap."""

    cap_usd: Decimal
    spent_usd: Decimal = field(default=Decimal(0))

    @property
    def remaining_usd(self) -> Decimal:
        return max(self.cap_usd - self.spent_usd, Decimal(0))

    def add(self, cost_usd: Decimal) -> None:
        self.spent_usd += cost_usd

    def check(self, run_id: str) -> None:
        if self.spent_usd >= self.cap_usd:
            raise BudgetExceededError(run_id, self.cap_usd, self.spent_usd)
