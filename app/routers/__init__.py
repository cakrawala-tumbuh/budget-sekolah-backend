from .organizations import router as organizations_router
from .assumptions import router as assumptions_router
from .grade_configs import router as grade_configs_router
from .expense_categories import router as expense_categories_router
from .investment_categories import router as investment_categories_router
from .income_categories import router as income_categories_router
from .budget_entries import router as budget_entries_router
from .income_entries import router as income_entries_router
from .investments import router as investments_router
from .depreciation import router as depreciation_router
from .contributions import router as contributions_router
from .parent_expense_allocations import router as parent_expense_allocations_router
from .simulation import router as simulation_router
from .auth import router as auth_router
from .users import router as users_router
from .database import router as database_router

__all__ = [
    "organizations_router",
    "assumptions_router",
    "grade_configs_router",
    "expense_categories_router",
    "investment_categories_router",
    "income_categories_router",
    "budget_entries_router",
    "income_entries_router",
    "investments_router",
    "depreciation_router",
    "contributions_router",
    "parent_expense_allocations_router",
    "simulation_router",
    "auth_router",
    "users_router",
    "database_router",
]
