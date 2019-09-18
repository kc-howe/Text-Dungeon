import tcod as tc
import tcod.event

from death_functions import kill_monster, kill_player
from entity import get_blocking_entities_at_location
from fov_functions import initialize_fov, recompute_fov
from game_messages import Message
from game_states import GameState
from input_handlers import handle_keys, handle_mouse, handle_main_menu
from loading_functions.data_loaders import load_game, save_game
from loading_functions.initialize_new_game import get_constants, get_game_variables
from menu import main_menu, message_box
from random_utils import from_dungeon_level
from render_functions import render_all, clear_all

def main():
    constants = get_constants()
    
    tc.console_set_custom_font('terminal10x10_gs_tc2.png', tc.FONT_TYPE_GREYSCALE | tc.FONT_LAYOUT_TCOD)
    
    con = tc.console.Console(constants['screen_width'], constants['screen_height'])
    panel = tc.console.Console(constants['screen_width'], constants['panel_height'])
    
    player = None
    entities = []
    game_map = None
    message_log = None
    game_state = None
    
    show_main_menu = True
    show_load_error_message = False
    
    main_menu_background_image = tc.image_load('menu_background.png')
    
    key = tc.Key()
    mouse = tc.Mouse()

    with tc.console_init_root(constants['screen_width'], constants['screen_height'], constants['window_title'], False) as root_console:
        while not tc.console_is_window_closed():
            tc.sys_check_for_event(tc.EVENT_KEY_PRESS | tc.EVENT_MOUSE, key, mouse)

            if show_main_menu:
                main_menu(con, main_menu_background_image, constants['screen_width'],
                          constants['screen_height'])
    
                if show_load_error_message:
                    message_box(con, 'No save game to load', 50, constants['screen_width'], constants['screen_height'])
    
                tc.console_flush()
    
                action = handle_main_menu(key)

                new_game = action.get('new_game')
                load_saved_game = action.get('load_saved_game')
                exit_game = action.get('exit')
    
                if show_load_error_message and (new_game or load_saved_game or exit_game):
                    show_load_error_message = False
                elif new_game:
                    player, entities, game_map, message_log, game_state = get_game_variables(constants)
                    game_state = GameState.PLAYER_TURN
    
                    show_main_menu = False
                elif load_saved_game:
                    try:
                        player, entities, game_map, message_log, game_state = load_game()
                        show_main_menu = False
                    except FileNotFoundError:
                        show_load_error_message = True
                elif exit_game:
                    break
    
            else:
                con.clear(fg=(63, 127, 63))
                play_game(player, entities, game_map, message_log, game_state, con, panel, constants)
                return True

def play_game(player, entities, game_map, message_log, game_state, con, panel, constants):
    fov_recompute = True
    
    fov_map = initialize_fov(game_map)
    
    key = tc.Key()
    mouse = tc.Mouse()
    
    game_state = GameState.PLAYER_TURN
    previous_game_state = game_state
    
    targeting_item = None
    
    while not tc.console_is_window_closed():
        tc.sys_check_for_event(tc.EVENT_KEY_PRESS | tc.EVENT_MOUSE, key, mouse)
        
        if fov_recompute:
            recompute_fov(fov_map, player.x, player.y, constants['fov_radius'], constants['fov_light_walls'], constants['fov_algorithm'])
        
        render_all(con, panel, entities, player, game_map, fov_map, fov_recompute, message_log, constants['screen_width'],
                   constants['screen_height'], constants['bar_width'], constants['panel_height'], constants['panel_y'], mouse, game_state)
        
        fov_recompute = False
        
        tc.console_flush()
        
        clear_all(con, entities)
        
        action = handle_keys(key, game_state)
        mouse_action = handle_mouse(mouse)
        
        move = action.get('move')
        wait = action.get('wait')
        pickup = action.get('pickup')
        show_inventory = action.get('show_inventory')
        drop_inventory = action.get('drop_inventory')
        inventory_index = action.get('inventory_index')
        take_stairs = action.get('take_stairs')
        level_up = action.get('level_up')
        show_character_screen = action.get('show_character_screen')
        main_menu = action.get('main_menu')
        exit = action.get('exit')
        quit_game = action.get('quit_game')
        fullscreen = action.get('fullscreen')    
        left_click = mouse_action.get('left_click')
        right_click = mouse_action.get('right_click')
        
        player_turn_results = []
        
        if move and game_state == GameState.PLAYER_TURN:
            player.turn_count = (player.turn_count + 1) % 100
            dx, dy = move
            destination_x = player.x + dx
            destination_y = player.y + dy
            
            if not game_map.is_blocked(destination_x, destination_y):
                target = get_blocking_entities_at_location(entities, destination_x, destination_y)
               
                if target:
                    attack_results = player.fighter.deal_damage(target)
                    player_turn_results.extend(attack_results)
                else:
                    if game_map.tiles[destination_x][destination_y].burning:
                        player_turn_results.append({'burn': True})
                    player.move(dx, dy)
                    fov_recompute = True
               
                game_state = GameState.ENEMY_TURN
                
        elif wait:
            if game_map.tiles[player.x][player.y].burning:
                player_turn_results.append({'burn': True})
            game_state = GameState.ENEMY_TURN
                
        elif pickup and game_state == GameState.PLAYER_TURN:
            for entity in entities:
                if entity.item and entity.x == player.x and entity.y == player.y:
                    pickup_results = player.inventory.add_item(entity)
                    player_turn_results.extend(pickup_results)
                    
                    break
        
        if show_inventory:
            previous_game_state = game_state
            game_state = GameState.SHOW_INVENTORY
        
        if drop_inventory:
            previous_game_state = game_state
            game_state = GameState.DROP_INVENTORY
        
        if inventory_index is not None and previous_game_state != GameState.PLAYER_DEAD and inventory_index < len(player.inventory.items):
            item = player.inventory.items[inventory_index]
            
            if game_state == GameState.SHOW_INVENTORY:
                player_turn_results.extend(player.inventory.use(item, entities=entities, fov_map=fov_map))
            else:
                player_turn_results.extend(player.inventory.drop(item))
        
        if game_state == GameState.TARGETING:
            if left_click:
                target_x, target_y = left_click
                
                item_use_results = player.inventory.use(targeting_item, entities=entities, fov_map=fov_map,
                                                        target_x=target_x, target_y=target_y)
                player_turn_results.extend(item_use_results)
            elif right_click:
                player_turn_results.append({'targeting_cancelled': True})
        
        if exit:
            if game_state in (GameState.SHOW_INVENTORY, GameState.DROP_INVENTORY, GameState.CHARACTER_SCREEN, GameState.PAUSE):
                game_state = previous_game_state
            elif game_state == GameState.TARGETING:
                player_turn_results.append({'targeting_cancelled': True})
            else:
                game_state = GameState.PAUSE
        
        if main_menu:
            save_game(player, entities, game_map, message_log, game_state)
            main()
        
        if fullscreen:
            tc.console_set_fullscreen(not tc.console_is_fullscreen())
        
        if quit_game:
            save_game(player, entities, game_map, message_log, game_state)
            break
        
        for player_turn_result in player_turn_results:            
            message = player_turn_result.get('message')
            dead_entity = player_turn_result.get('dead')
            item_added = player_turn_result.get('item_added')
            item_consumed = player_turn_result.get('consumed')
            item_dropped = player_turn_result.get('item_dropped')
            equip = player_turn_result.get('equip')
            targeting = player_turn_result.get('targeting')
            targeting_cancelled = player_turn_result.get('targeting_cancelled')
            xp = player_turn_result.get('xp')
            burn = player_turn_result.get('burn')
            
            if burn:
                player.burn(10, entities, message_log=message_log)
            
            if message:
                message_log.add_message(message)
                
            if dead_entity:
                if dead_entity == player:
                    message, game_state = kill_player(dead_entity)
                else:
                     message = kill_monster(dead_entity)
                
                message_log.add_message(message)
            
            if item_added:
                entities.remove(item_added)
                game_state = GameState.ENEMY_TURN
                        
            if item_consumed:
                game_state = GameState.ENEMY_TURN
            
            if item_dropped:
                entities.append(item_dropped)
                game_state = GameState.ENEMY_TURN
            
            if equip:
                equip_results = player.equipment.toggle_equip(equip)
                
                for equip_result in equip_results:
                    equipped = equip_result.get('equipped')
                    dequipped = equip_result.get('dequipped')
                    
                    if equipped:
                        message_log.add_message(Message('You equipped the {0}'.format(equipped.name)))
                    
                    if dequipped:
                        message_log.add_message(Message('You dequipped the {0}'.format(dequipped.name)))
                
                game_state = GameState.ENEMY_TURN
            
            if targeting:
                previous_game_state = GameState.PLAYER_TURN
                game_state = GameState.TARGETING
                
                targeting_item = targeting
                
                message_log.add_message(targeting_item.item.targeting_message)
            
            if targeting_cancelled:
                game_state = previous_game_state
                
                message_log.add_message(Message('Targeting cancelled'))
            
            if xp:
                leveled_up = player.level.add_xp(xp)
                message_log.add_message(Message('You gain {0} experience points.'.format(xp)))
                
                if leveled_up:
                    message_log.add_message(Message('Have you been working out? You look like you just reached level {0}'.format(
                            player.level.current_level) + '!', tc.yellow))
                    previous_game_state = game_state
                    game_state = GameState.LEVEL_UP

        
        if take_stairs and game_state == GameState.PLAYER_TURN:
            for entity in entities:
                if entity.stairs and entity.x == player.x and entity.y == player.y:
                    entities = game_map.next_floor(player, message_log, constants)
                    fov_map = initialize_fov(game_map)
                    fov_recompute = True
                    con.clear(fg=(63, 127, 63))
                    
                    break
        
        if level_up:
            if level_up == 'hp':
                player.fighter.base_max_hp += 20
                player.fighter.hp += 20
            elif level_up == 'att':
                player.fighter.base_attack += 1;
            elif level_up == 'str':
                player.fighter.base_strength += 1
            elif level_up == 'def':
                player.fighter.base_defense += 1
            
            game_state = previous_game_state
        
        if show_character_screen:
            previous_game_state = game_state
            game_state = GameState.CHARACTER_SCREEN
            
        
        if game_state == GameState.ENEMY_TURN:
            for entity in entities:
                if entity.ai:
                    enemy_turn_results = entity.ai.take_turn(player, fov_map, game_map, entities)
                    
                    for enemy_turn_result in enemy_turn_results:
                        message = enemy_turn_result.get('message')
                        dead_entity = enemy_turn_result.get('dead')
                        burn = enemy_turn_result.get('burn')
                        
                        if burn:
                            entity.burn(10, entities, message_log=message_log)
                            
                        if message:
                            message_log.add_message(message)
                        
                        if dead_entity:
                            if dead_entity == player:
                                message, game_state = kill_player(dead_entity)
                            else:
                                 message = kill_monster(dead_entity)
                            
                            message_log.add_message(message)
                            
                            if game_state == GameState.PLAYER_DEAD:
                                break
                            
                            
                    if game_state == GameState.PLAYER_DEAD:
                            break
            else:
                fov_recompute = True
                game_state = GameState.PLAYER_TURN
                
            
                    
        
if __name__ == '__main__':
    main()