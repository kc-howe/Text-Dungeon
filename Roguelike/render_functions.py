import tcod as tc

from enum import Enum

from game_states import GameState
from menu import character_screen, inventory_menu, level_up_menu, pause_menu
from random_utils import from_dungeon_level

class RenderOrder(Enum):
    STAIRS = 1
    CORPSE = 2
    ITEM = 3
    ACTOR = 4
    
def render_all(con, panel, entities, player, game_map, fov_map, fov_recompute, message_log, screen_width, screen_height, bar_width,
               panel_height, panel_y, mouse, game_state):
    
    # Define colors of walls and floors
    colors = {
        'dark_wall': from_dungeon_level([[tc.darkest_grey,1], [tc.desaturated_orange,4], [tc.darker_azure,7], [tc.darkest_fuchsia,10], [tc.darkest_flame,13]], game_map.dungeon_level),
        'dark_ground': from_dungeon_level([[tc.darker_sepia,1], [tc.darkest_grey,4], [tc.darkest_grey,7], [tc.darkest_sepia,10], [tc.darkest_grey,13]], game_map.dungeon_level),
        'light_wall': from_dungeon_level([[tc.dark_grey,1], [tc.brass,4], [tc.dark_azure,7], [tc.desaturated_fuchsia,10], [tc.dark_flame,13]], game_map.dungeon_level),
        'light_ground': from_dungeon_level([[tc.dark_sepia,1], [tc.darker_grey,4], [tc.darker_grey,7], [tc.darker_sepia,10], [tc.darker_grey,13]], game_map.dungeon_level),
        'burning_ground': tc.dark_flame
    }
    
    # Draw the game map
    if fov_recompute:
        for y in range(game_map.height):
            for x in range(game_map.width):
                game_map.tiles[x][y].take_turn()
                visible = tc.map_is_in_fov(fov_map, x, y)
                wall = game_map.tiles[x][y].block_sight
                if visible:
                    if wall:
                        tc.console_set_default_foreground(con, colors.get('light_wall'))
                        tc.console_put_char(con, x, y, '#', tc.BKGND_NONE)
                    elif game_map.tiles[x][y].burning:
                        tc.console_set_default_foreground(con, colors.get('burning_ground'))
                        tc.console_put_char(con, x, y, '_', tc.BKGND_NONE)
                    else:
                        tc.console_set_default_foreground(con, colors.get('light_ground'))
                        tc.console_put_char(con, x, y, '_', tc.BKGND_NONE)
                        
                    game_map.tiles[x][y].explored = True
                elif game_map.tiles[x][y].explored:
                    if wall:
                        tc.console_set_default_foreground(con, colors.get('dark_wall'))
                        tc.console_put_char(con, x, y, '#', tc.BKGND_NONE)
                    else:
                        tc.console_set_default_foreground(con, colors.get('dark_ground'))
                        tc.console_put_char(con, x, y, '_', tc.BKGND_NONE)
                    
    entities_in_render_order = sorted(entities, key=lambda x: x.render_order.value)
    
    # Draw all entities in the list
    for entity in entities_in_render_order:
        draw_entity(con, entity, fov_map, game_map, colors)
        
    tc.console_blit(con, 0, 0, screen_width, screen_height, 0, 0, 0)
    
    tc.console_set_default_background(panel, tc.black)
    tc.console_clear(panel)
    
    # Print game messages
    y = 1
    for message in message_log.messages:
        tc.console_set_default_foreground(panel, message.color)
        tc.console_print_ex(panel, message_log.x, y, tc.BKGND_NONE, tc.LEFT, message.text)
        y += 1
    
    render_bar(panel, 1, 3, bar_width, 'HP', player.fighter.hp, player.fighter.max_hp,
               tc.light_red, tc.darker_red)
    render_bar(panel, 1, 5, bar_width, 'XP', player.level.current_xp, player.level.experience_to_next_level,
               tc.light_green, tc.darker_green)
    tc.console_print_ex(panel, 1, 1, tc.BKGND_NONE, tc.LEFT, 'Dungeon level: {0}'.format(game_map.dungeon_level))
    
    tc.console_set_default_foreground(panel, tc.light_gray)
    tc.console_print_ex(panel, 1, 0, tc.BKGND_NONE, tc.LEFT,
                        get_names_under_mouse(mouse, entities, fov_map))
    
    tc.console_blit(panel, 0, 0, screen_width, panel_height, 0, 0, panel_y)
    
    if game_state in (GameState.SHOW_INVENTORY, GameState.DROP_INVENTORY):
        if game_state == GameState.SHOW_INVENTORY:
            inventory_title = 'Press the key next to an item to use it, or Esc to exit.\n'
        else:
            inventory_title = 'Press the key next to na item to drop it, or Esc to exit.\n'
            
        inventory_menu(con, inventory_title, player, 50, screen_width, screen_height)
    elif game_state == GameState.LEVEL_UP:
        level_up_menu(con, 'Level up! Choose a stat to raise:', player, 40, screen_width, screen_height)
    elif game_state == GameState.CHARACTER_SCREEN:
        character_screen(player, 30, 10, screen_width, screen_height)
    elif game_state == GameState.PAUSE:
        pause_menu(con, 'Game paused', 30, screen_width, screen_height)

def clear_all(con, entities):
    for entity in entities:
        clear_entity(con, entity)

def draw_entity(con, entity, fov_map, game_map, colors):
    if tc.map_is_in_fov(fov_map, entity.x, entity.y) or (entity.stairs and game_map.tiles[entity.x][entity.y].explored):
        tc.console_set_default_foreground(con, entity.color)
        tc.console_put_char(con, entity.x, entity.y, entity.char, tc.BKGND_NONE)
    elif game_map.tiles[entity.x][entity.y].explored:
        tc.console_set_default_foreground(con, colors.get('dark_ground'))
        tc.console_put_char(con, entity.x, entity.y, '_', tc.BKGND_NONE)

def clear_entity(con, entity):
    # Erase the character that represents this object
    tc.console_put_char(con, entity.x, entity.y, ' ', tc.BKGND_NONE)

def render_bar(panel, x, y, total_width, name, value, maximum, bar_color, back_color):
    bar_width = int(float(value) / maximum * total_width)
    
    tc.console_set_default_background(panel, back_color)
    tc.console_rect(panel, x, y, total_width, 1, False, tc.BKGND_SCREEN)
    
    tc.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        tc.console_rect(panel, x, y, bar_width, 1, False, tc.BKGND_SCREEN)
    
    tc.console_set_default_foreground(panel, tc.white)
    tc.console_print_ex(panel, int(x + total_width/2), y, tc.BKGND_NONE, tc.CENTER,
                        '{0}: {1}%'.format(name, int(100 * value / maximum)))

def get_names_under_mouse(mouse, entities, fov_map):
    (x, y) = (mouse.cx, mouse.cy)
    
    names = [entity.name for entity in entities
             if entity.x==x and entity.y==y and tc.map_is_in_fov(fov_map, entity.x, entity.y)]
    names = ', '.join(names)
    
    return names.capitalize()      