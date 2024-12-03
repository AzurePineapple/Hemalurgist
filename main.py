import pygame as pg
import pygame.display
import pygame.event
import pygame.sprite
import pygame.locals
from Classes import PlayerSprite, Object

# Define some global settings variables
FRAMERATE_CAP = 60
DISPLAY_FPS = True
WIDTH = 1080
HEIGHT = 720


pygame.init()


# Set up text
pygame.font.init()
font1 = pygame.font.SysFont("freesanbold.ttf", 50)
font2 = pygame.font.SysFont("chalkduster.ttf", 50)
DEBUG_FONT = pygame.font.SysFont("consolas", 20)

# Create clock object
clock = pygame.time.Clock()

# Create and name window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hemalurgist")


# Create list of all sprites
all_sprites = pygame.sprite.Group()

# Create player sprite
playerSprite = PlayerSprite((255, 0, 0), 30, 20, WIDTH, HEIGHT)
playerSprite.rect.x = 200
playerSprite.rect.y = 300

# Create object sprites
objectsGroup = pg.sprite.Group()
objectsGroup.add(Object(400, 300, 20, 20,  WIDTH, HEIGHT, True, 0.5))
objectsGroup.add(Object(500, 300, 20, 20, WIDTH, HEIGHT, True))
objectsGroup.add(Object(600, 300, 20, 20, WIDTH, HEIGHT, True, 20))
objectsGroup.add(Object(600, 300, 20, 20, WIDTH, HEIGHT, True, 2, True))


all_sprites.add(playerSprite, *objectsGroup)


# Game loopd
running = True

while running:
    # Set max framerate to 60
    clock.tick(FRAMERATE_CAP)

    screen.fill((0, 0, 0))

    # Display FPS in top left
    if DISPLAY_FPS:
        fps_text = DEBUG_FONT.render(
            str(int(clock.get_fps()))+"fps", True, (0, 255, 0))
        fps_rect = fps_text.get_rect()
        fps_rect.topleft = (5, 5)
        screen.blit(fps_text, fps_rect)

    ironMM_text = DEBUG_FONT.render(
        "metalmind storage: " + str(playerSprite.ironMetalMind), True, (0, 255, 0))
    ironMM_rect = ironMM_text.get_rect()
    ironMM_rect.topleft = (80, 5)
    screen.blit(ironMM_text, ironMM_rect)

    stage_text = DEBUG_FONT.render(
        "stage: " + str(playerSprite.fIron), True, (0, 255, 0))
    stage_rect = stage_text.get_rect()
    stage_rect.topright = (1060, 5)
    screen.blit(stage_text, stage_rect)

    weight_text = DEBUG_FONT.render(
        "mass:" + str(playerSprite.mass), True, (0, 255, 0))
    weight_rect = weight_text.get_rect()
    weight_rect.topleft = (800, 5)
    screen.blit(weight_text, weight_rect)

    # Detect inputs
    for event in pygame.event.get():
        if event.type == pg.QUIT:
            running = False
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_SPACE:
                playerSprite.jump()
            # Temp event triggers for working on laptop
            if event.key == pg.K_LEFT:
                playerSprite.aSteel = True
            if event.key == pg.K_RIGHT:
                playerSprite.aIron = True
            if event.key == pg.K_UP:
                playerSprite.changeMetalmindRate("iron", 1)
            if event.key == pg.K_DOWN:
                playerSprite.changeMetalmindRate("iron", -1)
            ###############################
        if event.type == pg.KEYUP:
            if event.key == pg.K_SPACE:
                playerSprite.releaseJump()

            # Temp event triggers for working on laptop
            if event.key == pg.K_LEFT:
                playerSprite.aSteel = False
            if event.key == pg.K_RIGHT:
                playerSprite.aIron = False
            ################################
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                playerSprite.aSteel = True
            if event.button == 3:
                playerSprite.aIron = True
            if event.button == 2:
                playerSprite.fIron = True
        if event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:
                playerSprite.aSteel = False
            if event.button == 3:
                playerSprite.aIron = False
            if event.button == 2:
                playerSprite.fIron = False

    # Handle movement input
    keys = pygame.key.get_pressed()
    if keys[pygame.K_a]:
        playerSprite.moveLeft()
    elif keys[pygame.K_d]:
        playerSprite.moveRight()
    else:
        playerSprite.stop()  # Decelerate when no key is pressed

    # Perform steelpush
    if playerSprite.aSteel:
        playerSprite.steelpush(objectsGroup)
    if playerSprite.aIron:
        playerSprite.ironpull(objectsGroup)
    # if playerSprite.fIron:
        # playerSprite.ironFeruchemy(1)

    all_sprites.update()
    all_sprites.draw(screen)

    for obj in objectsGroup:
        if obj.is_metallic:
            # Calculate the distance to determine if the line should be drawn
            dx = obj.rect.centerx - playerSprite.rect.centerx
            dy = obj.rect.centery - playerSprite.rect.centery
            distance = (dx**2 + dy**2) ** 0.5
            if distance <= playerSprite.maxPushRange:
                pygame.draw.line(screen, (100, 200, 255) if playerSprite.aSteel or playerSprite.aIron else (100, 100, 255),
                                 playerSprite.rect.center, obj.rect.center, 2)

    # Render blitted objects to screen
    pygame.display.flip()
