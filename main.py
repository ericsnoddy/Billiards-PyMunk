# std lib
from math import degrees, radians, atan2, cos, sin, ceil, sqrt

# reqs
import pygame as pg
import pymunk as pm
import pymunk.pygame_util as pgu


# game constants
WIDTH = 1200
HEIGHT = 678
FPS = 120
PANEL_HEIGHT = 50
ELASTICITY = 0.85
BALL_MASS = 4
BALL_DIAM = 36
BALL_RADIUS = BALL_DIAM / 2
CUEBALL_START_POS = (888, HEIGHT / 2)
POCKET_DIAM = 66
FRICTION = 400
FORCE_INCR_RATE = 100
MAX_FORCE = 15000
PWR_BAR_DIM = (10, 20)
PWR_BAR_BUFF = 4
PWR_BARS = 5  # should divide MAX_FORCE into whole parts
PWR_BAR_XOFF = -34
PWR_INCR = int(MAX_FORCE // PWR_BARS)

pg.init()
win = pg.display.set_mode((WIDTH, HEIGHT + PANEL_HEIGHT))
clock = pg.time.Clock()


# game variables
force = 0
force_direction = 1
shot_in_progress = False
powering_up = False
cueball_potted = False
potted_balls = []


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
            250 + (col * (BALL_DIAM - 4)), 
            267 + (row * BALL_DIAM + col * BALL_RADIUS)
        )
        new_ball = create_ball(BALL_RADIUS, pos)
        balls.append(new_ball)
    rows -= 1
# add cueball last; maintain insertion order
cue_ball = create_ball(BALL_RADIUS, CUEBALL_START_POS)
balls.append(cue_ball)



#create six pockets on table
pockets = [
  (55, 63),
  (592, 48),
  (1134, 64),
  (55, 616),
  (592, 629),
  (1134, 616)
]

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
power_bar = pg.Surface(PWR_BAR_DIM)
power_bar.fill('red')


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

        if e.type == pg.MOUSEBUTTONDOWN and not shot_in_progress:
            powering_up = True
        if e.type == pg.MOUSEBUTTONUP and powering_up:
            powering_up = False

    # DRAW

    # table
    win.fill('black')
    win.blit(bg_table, (0,0))

    # check if balls potted
    for i, ball in enumerate(balls):
        for pocket in pockets:
            ball_x_dist = abs(ball.body.position[0] - pocket[0])
            ball_y_dist = abs(ball.body.position[1] - pocket[1])
            ball_dist = sqrt(ball_x_dist ** 2 + ball_y_dist ** 2)
            if ball_dist < BALL_RADIUS:
                # check if cue ball
                if i == len(balls) - 1:  # last ball = cue ball
                    # hide the ball off screen until not shot_in_progress
                    cueball_potted = True
                    ball.body.position = (-100, -100)
                    ball.body.velocity = (0.0, 0.0)
                else:
                    space.remove(ball.body)
                    balls.remove(ball)
                    potted_balls.append(ball_images[i])
                    ball_images.pop(i)

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

    # cue stick        
    if not shot_in_progress:
        # reposition cueball if potted
        if cueball_potted:
            # reposition
            balls[-1].body.position = CUEBALL_START_POS
            cueball_potted = False

        # update cue angle from mouse_pos wrt cueball if balls not in motion
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
        for b in range(ceil(force / PWR_INCR)):
            win.blit(power_bar,
                (balls[-1].body.position[0] + PWR_BAR_XOFF + (b * (PWR_BAR_DIM[0] + PWR_BAR_BUFF)),
                balls[-1].body.position[1] + 30)
            )

    elif not powering_up and not shot_in_progress:
        x_impulse = -cos(radians(cue_angle))  # direction-vectors for applying force
        y_impulse = sin(radians(cue_angle))  
        balls[-1].body.apply_impulse_at_local_point((force * x_impulse, force * y_impulse), (0, 0))  # (0, 0) is rel. center of body
        force = 0

    # draw bottom panel
    pg.draw.rect(win, 'black', (0, HEIGHT, WIDTH, PANEL_HEIGHT))

    # draw potted balls in bottom panel
    for i, ball in enumerate(potted_balls):
        win.blit(ball, (10 + (i * 50), HEIGHT + 10))

    # show all the bodies/shapes
    # space.debug_draw(draw_options)  

    pg.display.set_caption(f'fps={clock.get_fps() :.1f}')
    pg.display.flip()
    
