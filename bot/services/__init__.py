from .combat_engine import BattleEngine
from .economy import EconomyService
from .energy_service import EnergyService
from .matchmaking import MatchmakingService
from .notification import NotificationService
from .ai_bot import AIBotService
# Services package - Add new services
try:
    from services.analytics import PlayerAnalytics, get_analytics
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

try:
    from services.visual_reporter import VisualReporter, get_visual_reporter
    VISUAL_REPORTER_AVAILABLE = True
except ImportError:
    VISUAL_REPORTER_AVAILABLE = False
  
