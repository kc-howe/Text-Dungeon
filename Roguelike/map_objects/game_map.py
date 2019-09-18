import tcod as tc

from random import randint

from components.ai import BasicRangedMonster, BasicMonster, ConfusedMonster
from components.equipment import EquipmentSlots
from components.equippable import Equippable
from components.fighter import Fighter
from components.item import Item
from components.stairs import Stairs
from entity import Entity
from game_messages import Message
from item_functions import cast_confuse, cast_fireball, cast_lightning, cast_projectile, heal
from map_objects.tile import Tile
from map_objects.rectangle import Rect
from random_utils import from_dungeon_level, random_choice_from_dict
from render_functions import RenderOrder

class GameMap:
    
    # Constructor
    def __init__(self, width, height, dungeon_level=1):
        self.width = width
        self.height = height
        self.tiles = self.initialize_tiles()
        self.dungeon_level = dungeon_level
    
    # Methods
    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False
    
    def create_room(self, room):
        # go through the tiles in the rectangle and make them passable
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.tiles[x][y].blocked = False
                self.tiles[x][y].block_sight = False
    
    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False
            
    def initialize_tiles(self):
        tiles = [[Tile(True) for y in range(self.height)] for x in range(self.width)]

        return tiles
    
    def is_blocked(self, x, y):
        if self.tiles[x][y].blocked:
            return True
        return False
    
    def is_burning(self, x, y):
        if self.tiles[x][y].burning:
            return True
        return False
    
    def make_map(self, max_rooms, room_min_size, room_max_size, map_width, map_height, player, entities):
        # Create two rooms for demonstration purposes
        rooms = []
        num_rooms = 0
        
        last_room_center_x = None
        last_room_center_y = None
        
        add_room_size = from_dungeon_level([[0,1], [2,4], [4,7], [6,10], [8,13]] , self.dungeon_level)
        for r in range(max_rooms):
            # random width and height
            w = randint(room_min_size, room_max_size + add_room_size)
            h = randint(room_min_size, room_max_size + add_room_size)
            # random position without going out of boundaries of the map
            x = randint(0, map_width - w - 1)
            y = randint(0, map_height - h - 1)
            
            new_room = Rect(x, y, w, h)
            
            # run through other rooms and see if they intersect with this one
            for other_room in rooms:
                if new_room.intersect(other_room):
                    break
            else:
                self.create_room(new_room)
                
                (new_x, new_y) = new_room.center()
                
                last_room_center_x  = new_x
                last_room_center_y = new_y
                
                if num_rooms == 0:
                    # if this is the first room, place the player here
                    player.x = new_x
                    player.y = new_y
                else:
                    # all rooms after the first, connect to the previous room with a tunnel
                    (prev_x, prev_y) = rooms[num_rooms-1].center()
                    
                    if randint(0,1)==1:
                        self.create_h_tunnel(prev_x, new_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        self.create_v_tunnel(prev_y, new_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, new_y)
                if num_rooms != 0:    
                    self.place_entities(new_room, entities)
                
                rooms.append(new_room)
                num_rooms += 1
        stairs_component = Stairs(self.dungeon_level + 1)
        down_stairs = Entity(last_room_center_x, last_room_center_y, '>', tc.white, 'Stairs',
                             render_order=RenderOrder.STAIRS, stairs=stairs_component)
        entities.append(down_stairs)
    
    def place_entities(self, room, entities):
        # Get a random number of monsters
        number_of_monsters = from_dungeon_level([[2,1], [3,4], [5,6], [7,8]], self.dungeon_level)
        number_of_items = from_dungeon_level([[1,1], [2,4], [3,6], [4,8]], self.dungeon_level)
        
        monster_chances = {
                'bat': from_dungeon_level([[20,1], [10,2], [5,3], [0,4]], self.dungeon_level),
                'demon': from_dungeon_level([[10,12], [10,15]], self.dungeon_level),
                'ghost': from_dungeon_level([[10,9], [30,11], [15,13]], self.dungeon_level),
                'goblin': from_dungeon_level([[10,3], [30,5], [15,8], [0,10]], self.dungeon_level),
                'hound': from_dungeon_level([[13,20]], self.dungeon_level),
                'infernal_skeleton': from_dungeon_level([[10,13]], self.dungeon_level),
                'skeleton': from_dungeon_level([[5,6], [10,7], [30,8], [15,11], [0,13]], self.dungeon_level),
                'slime': from_dungeon_level([[60,1], [30,5], [15,7], [0,9]], self.dungeon_level),
                'witch': from_dungeon_level([[5,9], [10,11], [0,13]], self.dungeon_level)
                }
        
        item_chances = {
                'arrow': from_dungeon_level([[20,2], [15,4], [10,7]], self.dungeon_level),
                'confusion_scroll': from_dungeon_level([[10,2]], self.dungeon_level),
                'fireball_scroll': from_dungeon_level([[20,8]], self.dungeon_level),
                'healing_potion': 35,
                'lightning_scroll': from_dungeon_level([[20,5]], self.dungeon_level),
                'none': from_dungeon_level([[60,1], [65,4], [50,7], [45,10]], self.dungeon_level),
                'buckler': from_dungeon_level([[5,4]], self.dungeon_level),
                'round_shield': from_dungeon_level([[5,7]], self.dungeon_level),
                'kite_shield': from_dungeon_level([[5,10]], self.dungeon_level),
                'tower_shield': from_dungeon_level([[5,13]], self.dungeon_level),
                'short_sword': from_dungeon_level([[5,5]], self.dungeon_level),
                'scimitar': from_dungeon_level([[5,8]], self.dungeon_level),
                'long_sword': from_dungeon_level([[5,11]], self.dungeon_level),
                'claymore': from_dungeon_level([[5,14]], self.dungeon_level)
                }
        
        for i in range(number_of_monsters):
            #Choose a random location in the room
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            
            if not any([entity for entity in entities if entity.x == x and entity.y ==y]):
                monster_choice = random_choice_from_dict(monster_chances)
                
                if monster_choice == 'skeleton':
                    level_bonus = from_dungeon_level([[0,6], [1,10]], self.dungeon_level)
                    fighter_component = Fighter(hp=40 + 10 * level_bonus,
                                                defense=4,
                                                strength=10 + level_bonus,
                                                attack=10 + level_bonus,
                                                xp=200 + 25 * level_bonus)
                    
                    ai_component = BasicMonster()
                    
                    monster = Entity(x, y, 'S', tc.lightest_sepia, 'skeleton', blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)
                    
                elif monster_choice == 'slime':
                    level_bonus = from_dungeon_level([[0,1], [1,4], [2,7]], self.dungeon_level)
                    fighter_component = Fighter(hp = 20 + 10 * level_bonus,
                                                defense = 0 + level_bonus // 2,
                                                strength = 4 + level_bonus,
                                                attack = 4 + level_bonus,
                                                xp = 35 + 25 * level_bonus)
                    
                    ai_component = BasicMonster()
                    
                    monster = Entity(x, y, 's', tc.desaturated_green, 'slime', blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)
                    
                elif monster_choice == 'bat':
                    fighter_component = Fighter(hp = 10,
                                                defense = 1,
                                                strength = 1,
                                                attack = 1,
                                                xp = 5)
                    
                    ai_component = ConfusedMonster()
                    
                    monster = Entity(x, y, 'b', tc.darker_azure, 'bat', blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)
                    
                elif monster_choice == 'goblin':
                    level_bonus = from_dungeon_level([[0,3], [1,7], [2,10]], self.dungeon_level)
                    fighter_component = Fighter(hp = 30 + 10 * level_bonus,
                                                defense = 2 + level_bonus // 2,
                                                strength = 8 + level_bonus,
                                                attack = 8 + level_bonus,
                                                xp = 100 + 25 * level_bonus)
                    
                    ai_component = BasicMonster()
                    
                    monster = Entity(x, y, 'G', tc.darker_green, 'goblin', blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)
                    
                elif monster_choice == 'ghost':
                    level_bonus = from_dungeon_level([[0,9], [1,13]], self.dungeon_level)
                    fighter_component = Fighter(hp = 20 + 10 * level_bonus,
                                                defense = 2,
                                                strength = 9 + level_bonus,
                                                attack = 9 + level_bonus, 
                                                xp = 85 + 25 * level_bonus)
                    
                    ai_component = BasicMonster()
                    
                    monster = Entity(x, y, 'g', tc.lightest_grey, 'ghost', blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)
                    
                elif monster_choice == 'witch':
                    fighter_component = Fighter(hp = 40,
                                                defense = 4,
                                                strength = 10,
                                                attack = 12, 
                                                xp = 150 + 25)
                    
                    ai_component = BasicRangedMonster(attack_roll=3)
                    
                    monster = Entity(x, y, 'W', tc.darker_purple, 'witch', blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)
                    
                elif monster_choice == 'hound':
                    fighter_component = Fighter(hp = 40,
                                                defense = 4,
                                                strength = 10,
                                                attack = 10,
                                                xp = 125)
                    
                    ai_component = BasicMonster()
                    
                    monster = Entity(x, y, 'h', tc.dark_sepia, 'hellhound', blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)
                    
                elif monster_choice == 'infernal_skeleton':
                    fighter_component = Fighter(hp = 60,
                                                defense = 6,
                                                strength = 18,
                                                attack = 18,
                                                xp = 300)
                    
                    ai_component = BasicMonster()
                    
                    monster = Entity(x, y, 'S', tc.dark_amber, 'infernal skeleton', blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)
                    
                else:
                    fighter_component = Fighter(hp = 80,
                                                defense = 8,
                                                strength = 24,
                                                attack = 24,
                                                xp = 600)
                    
                    ai_component = BasicMonster()
                    
                    monster = Entity(x, y, 'D', tc.dark_crimson, 'demon', blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)
                    
                entities.append(monster)
                
        for i in range(number_of_items):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            
            if not any([entity for entity in entities if entity.x == x and entity.y == y]):
                item_choice = random_choice_from_dict(item_chances)
                
                if item_choice == 'healing_potion':
                    item_component = Item(use_function=heal, amount=40)
                    item = Entity(x, y, '!', tc.celadon, 'Healing Potion', render_order = RenderOrder.ITEM,
                                  item=item_component)
                elif item_choice == 'arrow':
                    item_component = Item(use_function=cast_projectile, targeting=True, targeting_message=Message(
                            'Left-click a target to fire at, or right-click to cancel.', tc.light_cyan), damage=15)
                    item = Entity(x, y, '^', tc.gray, 'Arrow', render_order=RenderOrder.ITEM, item=item_component)
                elif item_choice == 'short_sword':
                    equippable_component = Equippable(EquipmentSlots.MAIN_HAND, str_bonus=3, att_bonus=2)
                    item = Entity(x, y, '/', tc.dark_orange, 'Short Sword', equippable=equippable_component)
                elif item_choice == 'scimitar':
                    equippable_component = Equippable(EquipmentSlots.MAIN_HAND, str_bonus=4, att_bonus=3)
                    item = Entity(x, y, '/', tc.dark_yellow, 'Scimitar', equippable=equippable_component)
                elif item_choice == 'long_sword':
                    equippable_component = Equippable(EquipmentSlots.MAIN_HAND, str_bonus=5, att_bonus=4)
                    item = Entity(x, y, '/', tc.dark_sky, 'Long Sword', equippable=equippable_component)
                elif item_choice == 'claymore':
                    equippable_component = Equippable(EquipmentSlots.MAIN_HAND, str_bonus=6, att_bonus=5)
                    item = Entity(x, y, '/', tc.gold, 'Claymore', equippable=equippable_component)
                elif item_choice == 'buckler':
                    equippable_component = Equippable(EquipmentSlots.OFF_HAND, def_bonus=1)
                    item = Entity(x, y, '[', tc.darker_orange, 'Buckler', equippable=equippable_component)
                elif item_choice == 'round_shield':
                    equippable_component = Equippable(EquipmentSlots.OFF_HAND, def_bonus=2)
                    item = Entity(x, y, '[', tc.darker_yellow, 'Round Shield', equippable=equippable_component)
                elif item_choice == 'kite_shield':
                    equippable_component = Equippable(EquipmentSlots.OFF_HAND, def_bonus=3)
                    item = Entity(x, y, '[', tc.darker_sky, 'Kite Shield', equippable=equippable_component)
                elif item_choice == 'tower_shield':
                    equippable_component = Equippable(EquipmentSlots.OFF_HAND, def_bonus=4)
                    item = Entity(x, y, '[', tc.brass, 'Tower Shield', equippable=equippable_component)
                elif item_choice == 'fireball_scroll':
                    item_component = Item(game_map=self, use_function=cast_fireball, targeting=True, targeting_message=Message(
                            'Left-cick a target to fire at, or right-click to cancel.', tc.light_cyan), damage=25, radius=3)
                    item = Entity(x, y, '?', tc.red, 'Fireball Scroll', render_order=RenderOrder.ITEM, item=item_component)
                elif item_choice == 'confusion_scroll':
                    item_component = Item(use_function=cast_confuse, targeting=True, targeting_message=Message(
                            'Left-cick an enemy to confuse it, or right-click to cancel.', tc.light_cyan))
                    item = Entity(x, y, '?', tc.light_pink, 'Confusion Scroll', render_order=RenderOrder.ITEM, item=item_component)
                elif item_choice == 'lightning_scroll':
                    item_component = Item(use_function=cast_lightning, damage=40, maximum_range=5)
                    item = Entity(x, y, '?', tc.yellow, 'Lightning Scroll', render_order=RenderOrder.ITEM,
                                  item=item_component)
                else:
                    continue
                
                entities.append(item)
                
    def next_floor(self, player, message_log, constants):
        self.dungeon_level += 1
        entities = [player]

        self.tiles = self.initialize_tiles()
        self.make_map(constants['max_rooms'], constants['room_min_size'], constants['room_max_size'],
                      constants['map_width'], constants['map_height'], player, entities)

        player.fighter.heal(player.fighter.max_hp // 2)

        message_log.add_message(Message('You take a moment to rest, and recover your strength.', tc.light_violet))

        return entities