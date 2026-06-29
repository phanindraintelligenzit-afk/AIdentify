"""API __init__ — re-export all routers."""

from api.health import router as health
from api.competitors import router as competitors
from api.signals import router as signals
from api.battlecards import router as battlecards
from api.briefings import router as briefings  # noqa: F401
