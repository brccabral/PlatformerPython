import pygame
from particles import ParticleEffect
from player import Player
from tiles import Tile
from settings import tile_size, screen_width

class Level:
    def __init__(self, level_data, surface: pygame.Surface) -> None:

        # level setup
        self.display_surface = surface
        self.setup_level(level_data)
        self.world_shift = 0
        self.current_x = 0

        # dust
        # it is single because we can't have jump and land at the same time
        self.dust_sprite = pygame.sprite.GroupSingle()
    
    def setup_level(self, layout):
        self.tiles = pygame.sprite.Group()
        self.player = pygame.sprite.GroupSingle()

        for row_index, row in enumerate(layout):
            for column_index, cell in enumerate(row):
                x = column_index * tile_size
                y = row_index * tile_size
                if cell == 'X':
                    tile = Tile((x,y), tile_size)
                    self.tiles.add(tile)
                if cell == 'P':
                    player_sprite: Player = Player((x,y), self.display_surface, self.create_jump_particles)
                    self.player.add(player_sprite)

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

    def run(self):
        # level tiles
        self.tiles.update(self.world_shift)
        self.tiles.draw(self.display_surface)

        # player
        self.horizontal_movement_collision()
        self.vertical_movement_collision()
        self.player.update()
        self.player.draw(self.display_surface)

        # dust particles
        self.dust_sprite.update(self.world_shift)
        self.dust_sprite.draw(self.display_surface)

        self.scroll_x()

    def horizontal_movement_collision(self):
        player: Player = self.player.sprite
        player.rect.x += player.direction.x * player.speed

        for sprite in self.tiles.sprites():
            if sprite.rect.colliderect(player.rect):
                if player.direction.x < 0:
                    player.rect.left = sprite.rect.right
                    player.on_right = True
                    self.current_x = sprite.rect.right
                    player.direction.x = 0
                elif player.direction.x > 0:
                    player.rect.right = sprite.rect.left
                    player.on_left = True
                    self.current_x = sprite.rect.left
                    player.direction.x = 0
        
        # avoid image offset pixels due to different image sizes for the animation
        if player.on_left and (player.rect.left < self.current_x or player.direction.x >= 0):
            player.on_left = False
        if player.on_right and(player.rect.right > self.current_x or player.direction.x <= 0):
            player.on_right = False
    
    def vertical_movement_collision(self):
        player: Player = self.player.sprite
        player.apply_gravity()

        for sprite in self.tiles.sprites():
            if sprite.rect.colliderect(player.rect):
                if player.direction.y < 0:
                    player.rect.top = sprite.rect.bottom
                    # if player touches ceiling, stops player's jump
                    player.direction.y = 0
                    player.on_ceiling = True
                elif player.direction.y > 0:
                    player.rect.bottom = sprite.rect.top
                    # prevent from crossing the tile if player keeps standing on it
                    player.direction.y = 0
                    player.on_ground = True

        if player.on_ground and (player.direction.y < 0 or player.direction.y > player.gravity):
            player.on_ground = False
        if player.on_ceiling and player.direction.y > 0:
            player.on_ceiling = False

    def create_jump_particles(self, pos):
        player_sprite: Player = self.player.sprite
        if player_sprite.facing_right:
            pos -= pygame.math.Vector2(15,5)
        else:
            pos += pygame.math.Vector2(-5,5)
        jump_particle_sprite = ParticleEffect(pos, 'jump')
        self.dust_sprite.add(jump_particle_sprite)
