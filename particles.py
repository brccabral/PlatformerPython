from typing import List
import pygame
from support import import_folder


class ParticleEffect(pygame.sprite.Sprite):
    def __init__(self, pos, particle_type, groups: List[pygame.sprite.Group]) -> None:
        super().__init__(groups)
        self.frame_index = 0
        self.animation_speed = 0.5
        if particle_type == 'jump':
            self.frames = import_folder(
                'assets/graphics/character/dust_particles/jump')
        if particle_type == 'land':
            self.frames = import_folder(
                'assets/graphics/character/dust_particles/land')
        if particle_type == 'explosion':
            self.frames = import_folder('assets/graphics/enemy/explosion')
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=pos)

    def animate(self):
        self.frame_index += self.animation_speed
        if self.frame_index >= len(self.frames):
            self.kill()
        else:
            self.image = self.frames[int(self.frame_index)]

    def run(self):
        self.animate()


if __name__ == '__main__':
    from main import main
    main()
