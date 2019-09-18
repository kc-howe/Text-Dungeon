import math
import tcod as tc

from components.ai import ConfusedMonster
from entity import Entity
from game_messages import Message


def heal(*args, **kwargs):
    entity = args[0]
    amount = kwargs.get('amount')

    results = []

    if entity.fighter.hp == entity.fighter.max_hp:
        results.append({'consumed': False, 'message': Message('You are already at full health', tc.yellow)})
    else:
        entity.fighter.heal(amount)
        results.append({'consumed': True, 'message': Message('Your wounds start to feel better!', tc.green)})

    return results

def cast_confuse(*args, **kwargs):
    entities = kwargs.get('entities')
    fov_map = kwargs.get('fov_map')
    target_x = kwargs.get('target_x')
    target_y = kwargs.get('target_y')
    
    results = []
    
    if not tc.map_is_in_fov(fov_map, target_x, target_y):
        results.append({'consumed': False, 'message': Message('You cannot target a tile outside your field of view.', tc.yellow)})
        return results
    
    for entity in entities:
        if entity.x == target_x and entity.y == target_y and entity.ai:
            confused_ai = ConfusedMonster(entity.ai, 10)
            
            confused_ai.owner = entity
            entity.ai = confused_ai
            
            results.append({'consumed': True, 'message': Message('The {0} is visibly confused, and begins to stumble!'.format(entity.name), tc.light_green)})
            
            break
    else:
        results.append({'consumed': False, 'message': Message('There is no targetable enemy there.', tc.yellow)})

    return results

def cast_fireball(*args, **kwargs):
    game_map = kwargs.get('game_map')
    entities = kwargs.get('entities')
    fov_map = kwargs.get('fov_map')
    damage = kwargs.get('damage')
    radius = kwargs.get('radius')
    target_x = kwargs.get('target_x')
    target_y = kwargs.get('target_y')
    
    results = []
    
    if not tc.map_is_in_fov(fov_map, target_x, target_y):
        results.append({'consumed': False, 'message': Message('You cannot target a tile outside your field of view.', tc.yellow)})
        return results
    
    results.append({'consumed': True, 'message': Message('The fireball explodes, burning everything within {0} tiles!'.format(radius), tc.orange)})
    
    for entity in entities:
        for y in range(game_map.height):
            for x in range(game_map.width):
                distance = math.sqrt((x-target_x)**2 + (y-target_y)**2)
                if distance <= radius:
                    game_map.tiles[x][y].burning = True
                    game_map.tiles[x][y].duration = (radius ** 2) - (distance ** 2) + 1
        if entity.distance(target_x, target_y) <= radius:
            results.extend(entity.burn(damage, entities))
    
    return results

def cast_lightning(*args, **kwargs):
    caster = args[0]
    entities = kwargs.get('entities')
    fov_map = kwargs.get('fov_map')
    damage = kwargs.get('damage')
    maximum_range = kwargs.get('maximum_range')
    
    results = []
    
    target = None
    closest_distance = maximum_range + 1
    
    for entity in entities:
        if entity.fighter and entity != caster and tc.map_is_in_fov(fov_map, entity.x, entity.y):
            distance = caster.distance_to(entity)
            
            if distance < closest_distance:
                target = entity
                closest_distance = distance
    if target:
        results.append({'consumed': True, 'target': target, 'message': Message('A lightning bolt strikes the {0} with loud thunder! The damage is {1}'.format(target.name, damage))})
        results.extend(target.fighter.take_damage(damage))
    else:
        results.append({'consumed': False, 'target': None, 'message': Message('There are no enemies close enough to strike.', tc.red)})
        
    return results

def cast_projectile(*args, **kwargs):
    entities = kwargs.get('entities')
    fov_map = kwargs.get('fov_map')
    damage = kwargs.get('damage')
    target_x = kwargs.get('target_x')
    target_y = kwargs.get('target_y')
    
    results = []
    
    if not tc.map_is_in_fov(fov_map, target_x, target_y):
        results.append({'consumed': False, 'message': Message('You cannot target a tile outside your field of view.', tc.yellow)})
        return results
    
    for entity in entities:
        if entity.x == target_x and entity.y == target_y and entity.fighter:
            results.append({'consumed': True, 'message': Message('The {0} is pierced by the arrow for {1} hit points.'.format(entity.name, damage))})
            results.extend(entity.fighter.take_damage(damage))
            break
    
    return results