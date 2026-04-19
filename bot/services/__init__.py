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
  
