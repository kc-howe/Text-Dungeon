class Equippable:
    def __init__(self, slot, att_bonus=0, str_bonus=0, def_bonus=0, max_hp_bonus=0):
        self.slot = slot
        self.att_bonus = att_bonus
        self.str_bonus = str_bonus
        self.def_bonus = def_bonus
        self.max_hp_bonus = max_hp_bonus