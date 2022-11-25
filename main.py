# std lib
from math import degrees, radians, atan2, cos, sin, ceil

# reqs
import pygame as pg
import pymunk as pm
import pymunk.pygame_util as pgu

pg.init()

WIDTH = 1200
HEIGHT = 678
FPS = 120

win = pg.display.set_mode((WIDTH, HEIGHT))
clock = pg.time.Clock()

# game constants
ELASTICITY = 0.8
BALL_MASS = 3
DIAM = 36
FRICTION = 300
FORCE_INCR_RATE = 100
MAX_FORCE = 10000
POWER_BARS = 5
POWER_INCR = int(MAX_FORCE // POWER_BARS)


# game variables
force = 0
force_direction = 1
shot_in_progress = False
powering_up = False


# load images
bg_table = pg.image.load('assets/images/table.png').convert()
cue_image = pg.image.load('assets/images/cue.png').convert_alpha()
ball_images = []
for i in range(1, 17):  # last ball is cue ball, 16.png
    ball_images.append(pg.image.load(f'assets/images/ball_{i}.png').convert_alpha())

# pymunk space
space = pm.Space()
static_body = space.static_body
draw_options = pgu.DrawOptions(win)


# FUNCTIONS
def create_ball(radius, pos):
    body = pm.Body()
    body.position = pos
    shape = pm.Circle(body, radius)
    shape.mass = BALL_MASS
    shape.elasticity = ELASTICITY
    # use pivot joint to add friction
    pivot = pm.PivotJoint(static_body, body, (0,0), (0,0))  # (0,0) rel center of each body
    pivot.max_bias = 0  # disable joint correction
    pivot.max_force = FRICTION  # emulate linear friction

    # shapes require bodies
    space.add(body, shape, pivot)
    return shape


def create_cushion(cush_coords):
    body = pm.Body(body_type=pm.Body.STATIC)
    body.position = (0, 0)
    shape = pm.Poly(body, cush_coords)
    shape.elasticity = ELASTICITY
    space.add(body, shape)



# setup game balls
balls = []
rows = 5
for col in range(5):
    for row in range(rows):
        pos = (
            250 + (col * (DIAM - 4)), 
            267 + (row * (DIAM + 1)) + (col * (DIAM / 2))
        )
        new_ball = create_ball(DIAM / 2, pos)
        balls.append(new_ball)
    rows -= 1
# add cueball last; maintain insertion order
cue_ball = create_ball(DIAM / 2, (888, HEIGHT / 2))
balls.append(cue_ball)

#create pool table cushions
cushions = [
  [(88, 56), (109, 77), (555, 77), (564, 56)],
  [(621, 56), (630, 77), (1081, 77), (1102, 56)],
  [(89, 621), (110, 600),(556, 600), (564, 621)],
  [(622, 621), (630, 600), (1081, 600), (1102, 621)],
  [(56, 96), (77, 117), (77, 560), (56, 581)],
  [(1143, 96), (1122, 117), (1122, 560), (1143, 581)]
]
for c in cushions:
    create_cushion(c)

##########################
class Cue:
    def __init__(self, pos):
        self.ORIG_IMG = cue_image
        self.angle = 0
        self.image = pg.transform.rotate(self.ORIG_IMG, self.angle)
        self.rect = self.image.get_rect(center=pos)


    def update(self, angle, pos):
        self.angle = angle
        self.rect.center = pos


    def draw(self, surf):
        self.image = pg.transform.rotate(self.ORIG_IMG, self.angle)
        # cue image has an added translucent length equal to cue length, allowing rotation about its center
        # but we have to offset the translucent bit by half its dimensions
        surf.blit(self.image,
            (self.rect.centerx - self.image.get_width() / 2,
            self.rect.centery - self.image.get_height() / 2)
        )

##########################
# create pool cue
cue = Cue(balls[-1].body.position)  # cueball is last in list

# power bars for the cue stick
power_bar = pg.Surface((10, 20))
power_bar.fill('red')

# #create six pockets on table
# pockets = [
#   (55, 63),
#   (592, 48),
#   (1134, 64),
#   (55, 616),
#   (592, 629),
#   (1134, 616)
# ]

#
# GAME LOOP
#
while True:

    # CLOCK MANAGEMENT
    clock.tick(FPS)
    space.step(1 / FPS)  # linking step functions ensures all Space() methods complete each game loop

    # EVENT LOOP
    for e in pg.event.get():
        if e.type == pg.QUIT:
            pg.quit()
            exit()

        if not shot_in_progress:
            if e.type == pg.MOUSEBUTTONDOWN:
                powering_up = True
            if e.type == pg.MOUSEBUTTONUP:
                powering_up = False

    # DRAW

    # table
    win.fill('black')
    win.blit(bg_table, (0,0))

    # pool balls
    for i, ball in enumerate(balls):
        pos = (
            ball.body.position[0] - ball.radius, 
            ball.body.position[1] - ball.radius
        )
        win.blit(ball_images[i], pos)

    # check balls in motion
    shot_in_progress = False
    for ball in balls:
        if int(ball.body.velocity[0]) != 0 or int(ball.body.velocity[1]) != 0:
            shot_in_progress = True

    # cue stick - 
        # update cue angle from mouse_pos wrt cueball if balls not in motion
    if not shot_in_progress:
        mouse_pos = pg.mouse.get_pos()
        x_dist = balls[-1].body.position[0] - mouse_pos[0]  # balls[-1] = cue ball
        y_dist = -(balls[-1].body.position[1] - mouse_pos[1])  # y-axis is reversed in pg
        cue_angle = degrees(atan2(y_dist, x_dist))
        
        cue.update(cue_angle, balls[-1].body.position)
        cue.draw(win)

    # power up the cue stick
    if powering_up:
        force += FORCE_INCR_RATE * force_direction
        # create a 'meter' that loops between min and max
        if force >= MAX_FORCE or force <= 0:
            force_direction *= -1
        # draw power bars
        for b in range(ceil(force / POWER_INCR)):
            pass

    elif not powering_up and not shot_in_progress:
        x_impulse = -cos(radians(cue_angle))  # direction-vectors for applying force
        y_impulse = sin(radians(cue_angle))  
        balls[-1].body.apply_impulse_at_local_point((force * x_impulse, force * y_impulse), (0, 0))  # (0, 0) is rel. center of body
        force = 0

    # show all the bodies/shapes
    # space.debug_draw(draw_options)  

    pg.display.set_caption(f'force={force}')
    # pg.display.set_caption(f'fps={clock.get_fps() :.1f}')
    pg.display.flip()
    
