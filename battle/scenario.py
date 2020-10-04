import json
from dataclasses import dataclass, field
from typing import Union

@dataclass
class Scenario:
    """シナリオ"""
    scenario_code : str
    player_lv: int
    enemies: list

    # Todo
    #boss: int
    #items: list

def load_scenarios(file_path:str)->list:
    """シナリオ情報を読み込む

    Args:
        file_path (str): 読み込み対象のJSONファイルパス

    Returns:
        list: 読み込み結果(シナリオのリスト)
    """
    with open(file=file_path, mode='r', encoding='utf-8') as f:
        sf = f.read()
        decode = json.JSONDecoder().decode(sf)
        scenarios = []
        for scenario in decode:
            scenarios.append(
                Scenario(
                    scenario_code=scenario["scenario_code"],
                    player_lv=scenario["player"]["lv"],
                    enemies=scenario["enemies"]["normal_enemies"],
                )
            )
        return scenarios
