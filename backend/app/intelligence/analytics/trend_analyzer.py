from typing import List, Dict, Any

class BiomarkerTrendAnalyzer:
    """
    Analyzes historical lab results over time to generate health trend insights.
    """
    def calculate_trend(self, data_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(data_points) < 2:
            return {"direction": "STABLE", "percentage_change": 0.0}
        
        first = data_points[0]["value"]
        last = data_points[-1]["value"]
        change = ((last - first) / first) * 100
        
        direction = "STABLE"
        if change > 5:
            direction = "INCREASING"
        elif change < -5:
            direction = "DECREASING"
            
        return {
            "direction": direction,
            "percentage_change": round(change, 2)
        }
