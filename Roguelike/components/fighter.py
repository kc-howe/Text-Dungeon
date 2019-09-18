import tcod as tc

from random import randint
from game_messages import Message

class Fighter:
    def __init__(self, hp, defense, strength, attack, xp=0):
        self.base_max_hp = hp
        self.base_defense = defense
        self.base_strength = strength
        self.base_attack = attack
        self.hp = hp
        self.xp = xp
    
    @property
    def max_hp(self):
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.max_hp_bonus
        else:
            bonus = 0
        
        return self.base_max_hp + bonus
    
    @property
    def strength(self):
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.str_bonus
        else:
            bonus = 0
        
        return self.base_strength + bonus
    
    @property
    def defense(self):
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.def_bonus
        else:
            bonus = 0
        
        return self.base_defense + bonus
    
    @property
    def attack(self):
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.att_bonus
        else:
            bonus = 0
        
        return self.base_attack + int(2.5*bonus)
    
    def take_damage(self, amount):
        results = []
        
        self.hp -= amount
        
        if self.hp <= 0:
            results.append({'dead': self.owner, 'xp': self.xp})
            
        return results
    
    def deal_damage(self, target):
        results = []
        
        attack_roll = randint(0, self.base_attack)
        
        if attack_roll == self.base_attack:
            attack_roll = target.fighter.defense
        
        if self.owner and self.owner.equipment:
            attack_roll += 2.5*self.owner.equipment.att_bonus
        
        if attack_roll - target.fighter.defense >= 0:
            strength_roll = randint(0, self.base_strength)
            target_defense_roll = randint(0, target.fighter.defense)
            
            damage = strength_roll - target_defense_roll
            
            if self.owner and self.owner.equipment:
                damage += self.owner.equipment.str_bonus
            
            if damage > 0:
                results.append({'message': Message('{0} attacks {1} for {2} hit points.'.format(self.owner.name.capitalize(), target.name, str(damage)), tc.white)})
                results.extend(target.fighter.take_damage(damage))
            else:
                results.append({'message': Message('{0} attacks {1} but does no damage.'.format(self.owner.name.capitalize(), target.name), tc.white)})
        else:
            results.append({'message': Message('{0} attacks {1} but misses.'.format(self.owner.name.capitalize(), target.name), tc.white)})
        
        return results
    
    def heal(self, amount):
        self.hp += amount
        
        if self.hp > self.max_hp:
            self.hp = self.max_hp