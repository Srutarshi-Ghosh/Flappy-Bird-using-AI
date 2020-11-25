import pygame
import neat
import time
import os
import random
import pickle
pygame.font.init()

WIDTH = 500
HEIGHT = 700
FPS = 50
GAME_VEL = 6

WHITE = (255, 255, 255)

STAT_FONT = pygame.font.SysFont("comicsans", 50)

pygame.init()
pygame.mixer.init()
game_folder = os.path.dirname(__file__)
image_folder = os.path.join(game_folder, 'Flappy_Bird_img')
BIRD_IMGS = [pygame.transform.scale(pygame.image.load(os.path.join(image_folder, 'bird{}.png'.format(i))), (40, 30)) for i in range(1, 4)]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join(image_folder, 'pipe.png')))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join(image_folder, 'base.png')))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join(image_folder, 'bg.png')))

class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -9.0
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        d = self.vel * self.tick_count + 1.5 * self.tick_count ** 2
        if d >= 16:
            d = 16
        if d < 0:
            d -= 2

        self.y = self.y + d

        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, surf):
        self.img_count += 1

        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        rotated_img = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_img.get_rect(center=self.img.get_rect(topleft = (self.x, self.y)).center)
        surf.blit(rotated_img, new_rect.topleft)

    def get_mask(self):
        return  pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 150

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= GAME_VEL

    def draw(self, surf):
        surf.blit(self.PIPE_TOP, (self.x, self.top))
        surf.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_TOP)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True

        return False


class Base:
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= GAME_VEL
        self.x2 -= GAME_VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, surf):
        surf.blit(self.IMG, (self.x1, self.y))
        surf.blit(self.IMG, (self.x2, self.y))


def draw_window(surf, bird, pipes, base, score):
    surf.blit(BG_IMG, (0, 0))
    for pipe in pipes:
        pipe.draw(surf)

    base.draw(surf)
    bird.draw(surf)

    text = STAT_FONT.render("Score: " + str(score), 1, (WHITE))
    surf.blit(text, (WIDTH - 10 - text.get_width(), 10))

    pygame.display.update()



pickle_in = open('Flappy_Bird.pickle', 'rb')
best = pickle.load(pickle_in)

net = best
bird = Bird(230, 350)


screen = pygame.display.set_mode((WIDTH, HEIGHT))
base = Base(630)
pipes = [Pipe(700)]
clock = pygame.time.Clock()
score = 0


running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            pygame.quit()
            quit()

    pipe_ind = 0
    if bird and len(pipes) > 1 and bird.x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
        pipe_ind = 1

    bird.move()

    output = net.activate((bird.y, abs(bird.y + pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

    if output[0] > 0.5:
        bird.jump()

    rem = []
    add_pipe = False
    for pipe in pipes:

        if pipe.collide(bird):
            running = False

        if not pipe.passed and pipe.x < bird.x:
            pipe.passed = True
            add_pipe = True

        if pipe.x + pipe.PIPE_TOP.get_width() < 0:
            rem.append(pipe)

        pipe.move()

    if add_pipe:
        score += 1
        pipes.append(Pipe(700))

    for r in rem:
        pipes.remove(r)

    if bird.y + bird.img.get_height() >= base.y or bird.y < 0:
        running = False


    base.move()
    draw_window(screen, bird, pipes, base, score)










