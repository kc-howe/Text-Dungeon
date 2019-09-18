import tcod as tc

from random import randint

from game_messages import Message
#from random_utils import from_dungeon_level

class BasicMonster:
    def take_turn(self, target, fov_map, game_map, entities):
        results = []
        
        monster = self.owner
        if tc.map_is_in_fov(fov_map, monster.x, monster.y):
            
            if monster.distance_to(target) >= 2:
                monster.move_astar(target, entities, game_map)
                if game_map.tiles[monster.x][monster.y].burning:
                    results.append({'burn': True})
                
            elif target.fighter.hp > 0:
                attack_results = monster.fighter.deal_damage(target)
                results.extend(attack_results)
        
        else:
            monster.move_random(game_map, entities, 5)
            if game_map.tiles[monster.x][monster.y].burning:
                results.append({'burn': True})
        
        return results

class BasicRangedMonster:
    def __init__(self, attack_roll):
        self.attack_roll = attack_roll
    
    def take_turn(self, target, fov_map, game_map, entities):
        results = []
        
        monster = self.owner
        if tc.map_is_in_fov(fov_map, monster.x, monster.y):
            attack_chance = randint(0, self.attack_roll)
            
            if target.fighter.hp > 0 and attack_chance == self.attack_roll - 1:
                attack_results = monster.fighter.deal_damage(target)
                results.extend(attack_results)
                
            elif monster.distance_to(target) >= 4:
                monster.move_astar(target, entities, game_map)
                if game_map.tiles[monster.x][monster.y].burning:
                    results.append({'burn': True})
        
        else:
            monster.move_random(game_map, entities, 5)
            if game_map.tiles[monster.x][monster.y].burning:
                results.append({'burn': True})
            
        return results

class ConfusedMonster:
    def __init__(self, previous_ai=None, number_of_turns=10):
        self.previous_ai = previous_ai
        self.number_of_turns = number_of_turns
        
    def take_turn(self, target, fov_map, game_map, entities):
        results = []
        
        monster = self.owner
        if self.number_of_turns > 0:
            monster.move_random(game_map, entities, 2)
            if game_map.tiles[monster.x][monster.y].burning:
                results.append({'burn': True})
            
            if self.previous_ai is not None:
                self.number_of_turns -= 1
        else:
            if self.previous_ai is not None:
                self.owner.ai = self.previous_ai
                results.append({'message': Message('The {0} is no longer confused!'.format(self.owner.name), tc.red)})
        
        return results