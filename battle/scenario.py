import json
from dataclasses import dataclass, field
from typing import Union

@dataclass
class Scenario:
    """シナリオ"""
    # Todo:playerやenemiesは別のデータクラスに切り出すことを検討する
    scenario_code : str
    player_lv: int
    enemies: list
    boss: int

def scenario_decode(json_object:dict)->Scenario:
    """ScenarioのJSONをデコードする

    Args:
        json_object (dict): JSONのオブジェクト

    Returns:
        Scenario: JSONからデコードしたScenarioインスタンス
    """
    return Scenario(
        scenario_code=json_object['scenario_code'],
        player_lv=json_object['player_lv'],
        enemies=json_object['normal_enemies'],
        boss=json_object['boss'],
    )

def load_scenarios(file_path:str)->Union[list, Scenario]:
    """シナリオ情報を読み込む

    Args:
        file_path (str): 読み込み対象のJSONファイルパス

    Returns:
        list: 読み込み結果(シナリオのリスト)
    """
    with open(file=file_path, mode='r', encoding='utf-8') as f:
        sf = f.read()
        decode = json.JSONDecoder(object_hook=scenario_decode).decode(sf)
        return decode
