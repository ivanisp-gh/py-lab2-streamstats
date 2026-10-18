import json


def format_json_report(stats_dict: dict) -> str:
    """Преобразует статистику в JSON."""
    return json.dumps(stats_dict, indent=2, ensure_ascii=False) 