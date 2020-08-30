from dataclasses import dataclass, field

@dataclass
class Weapon():
    name:str
    attack:int

@dataclass
class Armor():
    name:str
    difense:int

@dataclass
class Shield():
    name:str
    difense:int

class Items():
    weapons = {
        'none': Weapon(name='素手', attack=0),
        'club': Weapon(name='棍棒', attack=4),
        'copper_sword': Weapon(name='銅の剣', attack=10),
        'iron_ax': Weapon(name='鉄の斧', attack=15),
        'steel_sword': Weapon(name='鋼の剣', attack=20),
    }

    armors = {
        'none': Armor(name='なし', difense=0),
        'leather': Armor(name='皮の服', difense=4),
        'chain': Armor(name='鎖帷子', difense=10),
        'iron': Armor(name='鉄の鎧', difense=15),
        'steel': Armor(name='鋼の鎧', difense=20),
    }

    shields = {
        'none': Shield(name='なし', difense=0),
        'leather': Shield(name='皮の盾', difense=4),
        'iron': Shield(name='鉄の盾', difense=10),
    }
