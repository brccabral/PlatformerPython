import pygame
from decoration import Clouds, Sky, Water
from enemy import Enemy
from particles import ParticleEffect
from player import Player
from tiles import Coin, Crate, Palm, StaticTile, Tile
from settings import tile_size, screen_width, screen_height, CAMERA_BORDERS
from support import import_csv_layout, import_cut_graphics, resource_path
from typing import Callable, List
from game_data import levels

class Level:
    def __init__(self, current_level: int, surface: pygame.Surface, create_overworld: Callable, change_coins: Callable, change_health: Callable) -> None:

        # general setup
        self.display_surface = surface
        self.current_level = current_level
        self.world_shift = 0

        # sprite group setup
        # sprites in this group will be diplayed, other won't
        self.visible_sprites = CameraGroup()
        # sprites in this group will be updated, others will remain static
        self.active_sprites = pygame.sprite.Group()
        # sprites in this group will collide with player
        self.collision_sprites = pygame.sprite.Group()

        # level setup
        level_data = levels[current_level]
        level_content = level_data['content'] # level title
        self.new_max_level = level_data['unlock']
        self.create_overworld = create_overworld

        # level display
        self.font = pygame.font.Font(None, 40)
        self.text_surface = self.font.render(level_content, True, 'White')
        self.text_rect = self.text_surface.get_rect(center = (screen_width//2, 20))

        # terrain setup
        terrain_layout = import_csv_layout(level_data['terrain'])
        self.create_tile_group(terrain_layout, 'terrain')

        # grass setup
        grass_layout = import_csv_layout(level_data['grass'])
        self.create_tile_group(grass_layout, 'grass')
        
        # crates setup
        crates_layout = import_csv_layout(level_data['crates'])
        self.create_tile_group(crates_layout, 'crates')
        
        # crates setup
        coins_layout = import_csv_layout(level_data['coins'])
        self.create_tile_group(coins_layout, 'coins')
        
        # foreground palms setup
        fg_palms_layout = import_csv_layout(level_data['fg_palms'])
        self.create_tile_group(fg_palms_layout, 'fg_palms')
        
        # background palms setup
        bg_palms_layout = import_csv_layout(level_data['bg_palms'])
        self.create_tile_group(bg_palms_layout, 'bg_palms')

        # enemy setup
        enemies_layout = import_csv_layout(level_data['enemies'])
        self.create_tile_group(enemies_layout, 'enemies')

        # constraint
        constraints_layout = import_csv_layout(level_data['constraints'])
        self.create_tile_group(constraints_layout, 'constraints')

        # player setup
        player_layout = import_csv_layout(level_data['player'])
        self.create_tile_group(player_layout, 'player', change_health)
        # self.player_setup(player_layout, change_health)
        

        # dust
        # it is single because we can't have jump and land at the same time
        self.dust_sprite = pygame.sprite.GroupSingle()
        self.player_on_ground = False

        # explosion particles
        self.explosion_sprites = pygame.sprite.Group()

        # decoration
        self.sky = Sky(8)
        level_width = len(terrain_layout[0]) * tile_size
        self.water = Water(screen_height - 20, level_width, [self.visible_sprites])
        self.clouds = Clouds(400, level_width, 20, [self.visible_sprites])

        # ui
        self.change_coins = change_coins
        # audio
        self.coin_sound = pygame.mixer.Sound(resource_path('assets/audio/effects/coin.wav'))
        self.stomp_sound = pygame.mixer.Sound(resource_path('assets/audio/effects/stomp.wav'))

    
    # def player_setup(self, layout: list, change_health: Callable):
    #     for row_index, row in enumerate(layout):
    #         for column_index, cell in enumerate(row):
    #             x = column_index * tile_size
    #             y = row_index * tile_size
    #             if cell == '0':
    #                 sprite = Player((x,y), self.display_surface, self.create_jump_particles, change_health)
    #                 self.player.add(sprite)
    #             if cell == '1':
    #                 hat_surface = pygame.image.load(resource_path('assets/graphics/character/hat.png')).convert_alpha()
    #                 sprite = StaticTile((x,y), tile_size, hat_surface)
    #                 self.goal.add(sprite)

    def create_tile_group(self, layout: List, layout_type: str, change_health: Callable = None):
        if layout_type == 'terrain':
            terrain_tile_list = import_cut_graphics(resource_path('assets/graphics/terrain/terrain_tiles.png'))
        if layout_type == 'grass':
            grass_tile_list = import_cut_graphics(resource_path('assets/graphics/decoration/grass/grass.png'))
        
        for row_index, row in enumerate(layout):
            for column_index, cell in enumerate(row):
                x = column_index * tile_size
                y = row_index * tile_size
                if cell != '-1':
                    if layout_type == 'terrain':
                        tile_surface = terrain_tile_list[int(cell)]
                        StaticTile((x,y), tile_size, tile_surface, [self.visible_sprites, self.collision_sprites])
                    if layout_type == 'grass':
                        tile_surface = grass_tile_list[int(cell)]
                        StaticTile((x,y), tile_size, tile_surface, [self.visible_sprites])
                    if layout_type == 'crates':
                        Crate((x,y), tile_size, [self.visible_sprites, self.collision_sprites])
                    if layout_type == 'coins':
                        if cell == '0':
                            Coin((x,y), tile_size, 'assets/graphics/coins/gold', 5, [self.visible_sprites])
                        else:
                            Coin((x,y), tile_size, 'assets/graphics/coins/silver', 1, [self.visible_sprites])
                    if layout_type == 'fg_palms':
                        if cell == '0': Palm((x,y), tile_size, 'assets/graphics/terrain/palm_small', 38, [self.visible_sprites, self.collision_sprites])
                        if cell == '1': Palm((x,y), tile_size, 'assets/graphics/terrain/palm_large', 64, [self.visible_sprites, self.collision_sprites])
                    if layout_type == 'bg_palms':
                        Palm((x,y), tile_size, 'assets/graphics/terrain/palm_bg', 64, [self.visible_sprites])
                    if layout_type == 'enemies':
                        Enemy((x,y), tile_size, [self.visible_sprites])
                    if layout_type == 'constraints':
                        Tile((x,y), tile_size, [self.collision_sprites])
                    if layout_type == 'player':
                        if cell == '0':
                            self.player = Player((x,y), 
                                self.display_surface, 
                                self.create_jump_particles, 
                                change_health,
                                [self.visible_sprites, self.active_sprites],
                                self.collision_sprites
                                )
                        if cell == '1':
                            hat_surface = pygame.image.load(resource_path('assets/graphics/character/hat.png')).convert_alpha()
                            self.goal = StaticTile((x,y), tile_size, hat_surface, [self.visible_sprites])


    def scroll_x(self):
        player: Player = self.player.sprite
        player_x = player.rect.centerx
        direction_x = player.direction.x

        if player_x < screen_width//4 and direction_x < 0:
            self.world_shift = 8
            player.speed = 0
        elif player_x > screen_width-(screen_width//4) and direction_x > 0:
            self.world_shift = -8
            player.speed = 0
        else:
            self.world_shift = 0
            player.speed = 8

    def input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
            # unlocks new level
            self.create_overworld(self.current_level, self.new_max_level)
        if keys[pygame.K_ESCAPE]:
            # keep new level unchanged
            self.create_overworld(self.current_level, 0)

    def run(self):
        # self.input()
        self.sky.draw(self.display_surface)
        self.display_surface.blit(self.text_surface, self.text_rect)

        self.active_sprites.update()
        self.visible_sprites.custom_draw(self.player)

        # self.enemy_constraint_collision()
        
        # player
        # self.horizontal_movement_collision()
        # self.get_player_on_ground() # this needs to be before vertical collision
        # self.vertical_movement_collision()
        # self.create_landing_dust() # this needs to be after vertical collision
        # self.check_coin_collisions()
        # self.check_enemy_collisions()

        # self.water.draw(self.display_surface, self.world_shift)

        # self.scroll_x()

        # self.check_death()
        # self.check_win()

    def horizontal_movement_collision(self):
        player: Player = self.player.sprite
        player.collision_rect.x += player.direction.x * player.speed

        collidable_sprites = self.terrain_sprites.sprites() + self.crates_sprites.sprites() + self.fg_palms_sprites.sprites()
        for sprite in collidable_sprites:
            if sprite.rect.colliderect(player.collision_rect):
                if player.direction.x < 0:
                    player.collision_rect.left = sprite.rect.right
                    player.direction.x = 0
                elif player.direction.x > 0:
                    player.collision_rect.right = sprite.rect.left
                    player.direction.x = 0
    
    def vertical_movement_collision(self):
        player: Player = self.player.sprite
        player.apply_gravity()

        collidable_sprites = self.terrain_sprites.sprites() + self.crates_sprites.sprites() + self.fg_palms_sprites.sprites()
        for sprite in collidable_sprites:
            if sprite.rect.colliderect(player.collision_rect):
                if player.direction.y < 0:
                    player.collision_rect.top = sprite.rect.bottom
                    # if player touches ceiling, stops player's jump
                    player.direction.y = 0
                elif player.direction.y > 0:
                    player.collision_rect.bottom = sprite.rect.top
                    # prevent from crossing the tile if player keeps standing on it
                    player.direction.y = 0
                    player.on_ground = True

        if player.on_ground and (player.direction.y < 0 or player.direction.y > player.gravity):
            player.on_ground = False

    def enemy_constraint_collision(self):
        enemy: Enemy
        for enemy in self.enemies_sprites.sprites():
            if pygame.sprite.spritecollide(enemy, self.constraints_sprites, dokill=False):
                enemy.reverse()

    def check_death(self):
        if self.player.sprite.rect.top > screen_height:
            self.create_overworld(self.current_level, 0)

    def check_win(self):
        if pygame.sprite.spritecollide(self.player.sprite, self.goal, False):
            self.create_overworld(self.current_level, self.new_max_level)

    def create_jump_particles(self, pos):
        if self.player.sprite.facing_right:
            pos -= pygame.math.Vector2(15,5)
        else:
            pos += pygame.math.Vector2(-5,5)
        jump_particle_sprite = ParticleEffect(pos, 'jump')
        self.dust_sprite.add(jump_particle_sprite)

    def get_player_on_ground(self):
        # save the on_ground state before the vertical collision
        # if there is a collision after, it means the player
        # was on the air
        self.player_on_ground = self.player.sprite.on_ground
    
    def create_landing_dust(self):
        # check if player was on the air before the vertical collision
        if not self.player_on_ground and self.player.sprite.on_ground and not self.dust_sprite.sprites():
            if self.player.sprite.facing_right:
                offset = pygame.math.Vector2(10,15)
            else:
                offset = pygame.math.Vector2(-10,15)
            fall_dust_particle = ParticleEffect(self.player.sprite.rect.midbottom - offset, 'land')
            self.dust_sprite.add(fall_dust_particle)
    
    def check_coin_collisions(self):
        collided_coins: List[Coin] = pygame.sprite.spritecollide(self.player.sprite, self.coins_sprites, True)
        if collided_coins:
            self.coin_sound.play()
            for coin in collided_coins:
                self.change_coins(coin.value)

    def check_enemy_collisions(self):
        enemy_collisions: List[Enemy] = pygame.sprite.spritecollide(self.player.sprite, self.enemies_sprites, False)

        if enemy_collisions:
            for enemy in enemy_collisions:
                enemy_center = enemy.rect.centery
                enemy_top = enemy.rect.top
                player_bottom = self.player.sprite.rect.bottom
                if enemy_top < player_bottom < enemy_center and self.player.sprite.direction.y > 0:
                    self.stomp_sound.play()
                    self.player.sprite.direction.y = -15
                    explosion_sprite = ParticleEffect(enemy.rect.center, 'explosion')
                    self.explosion_sprites.add(explosion_sprite)
                    enemy.kill()
                else:
                    self.player.sprite.get_damage()



class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.math.Vector2(100, 300)

        # center camera setup
        # camera follows Player always
        # Player always on the center

        self.half_width = self.display_surface.get_size()[0] // 2
        self.half_height = self.display_surface.get_size()[1] // 2

        # box camera
        # camera moves if Player reaches border of screen

        camera_left = CAMERA_BORDERS['left']
        camera_top = CAMERA_BORDERS['top']
        camera_width = self.display_surface.get_size(
        )[0] - (camera_left + CAMERA_BORDERS['right'])
        camera_height = self.display_surface.get_size(
        )[1] - (camera_top + CAMERA_BORDERS['bottom'])

        self.camera_rect = pygame.Rect(
            camera_left, camera_top, camera_width, camera_height)

    def offset_from_player(self, player: Player):
        # player offset
        self.offset.x = player.rect.centerx - self.half_width
        self.offset.y = player.rect.centery - self.half_height

    def offset_from_level(self, player: Player):

        # camera offset
        if player.rect.left < self.camera_rect.left:
            self.camera_rect.left = player.rect.left
        if player.rect.right > self.camera_rect.right:
            self.camera_rect.right = player.rect.right
        if player.rect.top < self.camera_rect.top:
            self.camera_rect.top = player.rect.top
        if player.rect.bottom > self.camera_rect.bottom:
            self.camera_rect.bottom = player.rect.bottom
        self.offset = pygame.math.Vector2(
            self.camera_rect.left - CAMERA_BORDERS['left'],
            self.camera_rect.top - CAMERA_BORDERS['top'])

    def custom_draw(self, player: Player):

        # self.offset_from_player(player)
        self.offset_from_level(player)

        for sprite in self.sprites():
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_pos)



if __name__ == '__main__':
    from main import main
    main()
