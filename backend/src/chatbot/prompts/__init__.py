"""
Módulo de prompts del chatbot RIM - MVP v2.3.

Contiene todos los templates de prompts y utilidades relacionadas:
- diagnostic_prompt: Prompts para diagnóstico de problemas
- maintenance_prompt: Prompts para recomendaciones de mantenimiento
- explanation_prompt: Prompts para explicaciones educativas
- title_generator: Generación automática de títulos de conversaciones
- ml_analysis_prompt: Análisis ML completo y predicciones (NEW v2.3)
- trip_analysis_prompt: Análisis de viajes y patrones de conducción (NEW v2.3)
- freemium_prompt: Comparativas Free vs Pro y upselling (NEW v2.3)
- sensor_prompt: Lectura e interpretación de sensores en tiempo real (NEW v2.3)
"""
from src.chatbot.prompts.diagnostic_prompt import (
    DIAGNOSTIC_SYSTEM_PROMPT,
    build_diagnostic_prompt,
    build_quick_diagnostic_prompt
)
from src.chatbot.prompts.maintenance_prompt import (
    MAINTENANCE_SYSTEM_PROMPT,
    build_maintenance_recommendation_prompt
)
from src.chatbot.prompts.explanation_prompt import (
    EXPLANATION_SYSTEM_PROMPT,
    build_explanation_prompt
)
from src.chatbot.prompts.title_generator import (
    generate_conversation_title,
    generate_simple_title
)
from src.chatbot.prompts.ml_analysis_prompt import (
    ML_ANALYSIS_SYSTEM_PROMPT,
    build_ml_analysis_report_prompt,
    build_quick_ml_summary_prompt,
    build_component_specific_analysis_prompt
)
from src.chatbot.prompts.trip_analysis_prompt import (
    TRIP_ANALYSIS_SYSTEM_PROMPT,
    build_trip_summary_prompt,
    build_trip_pattern_analysis_prompt,
    build_fuel_efficiency_analysis_prompt
)
from src.chatbot.prompts.freemium_prompt import (
    FREEMIUM_COMPARISON_SYSTEM_PROMPT,
    build_plan_comparison_prompt,
    build_limit_reached_prompt,
    build_feature_discovery_prompt,
    build_smart_upsell_prompt
)
from src.chatbot.prompts.sensor_prompt import (
    SENSOR_READING_SYSTEM_PROMPT,
    build_sensor_reading_prompt,
    build_multi_sensor_dashboard_prompt,
    build_sensor_trend_analysis_prompt,
    build_anomaly_alert_prompt
)

__all__ = [
    # Diagnostic prompts
    "DIAGNOSTIC_SYSTEM_PROMPT",
    "build_diagnostic_prompt",
    "build_quick_diagnostic_prompt",
    
    # Maintenance prompts
    "MAINTENANCE_SYSTEM_PROMPT",
    "build_maintenance_recommendation_prompt",
    
    # Explanation prompts
    "EXPLANATION_SYSTEM_PROMPT",
    "build_explanation_prompt",
    
    # Title generation
    "generate_conversation_title",
    "generate_simple_title",
    
    # ML Analysis prompts (NEW v2.3)
    "ML_ANALYSIS_SYSTEM_PROMPT",
    "build_ml_analysis_report_prompt",
    "build_quick_ml_summary_prompt",
    "build_component_specific_analysis_prompt",
    
    # Trip Analysis prompts (NEW v2.3)
    "TRIP_ANALYSIS_SYSTEM_PROMPT",
    "build_trip_summary_prompt",
    "build_trip_pattern_analysis_prompt",
    "build_fuel_efficiency_analysis_prompt",
    
    # Freemium prompts (NEW v2.3)
    "FREEMIUM_COMPARISON_SYSTEM_PROMPT",
    "build_plan_comparison_prompt",
    "build_limit_reached_prompt",
    "build_feature_discovery_prompt",
    "build_smart_upsell_prompt",
    
    # Sensor prompts (NEW v2.3)
    "SENSOR_READING_SYSTEM_PROMPT",
    "build_sensor_reading_prompt",
    "build_multi_sensor_dashboard_prompt",
    "build_sensor_trend_analysis_prompt",
    "build_anomaly_alert_prompt",
]
