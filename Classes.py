import random
from turtle import xcor
import pygame


class PlayerSprite(pygame.sprite.Sprite):
    def __init__(self, color, height, width, screenWidth, screenHeight, maxPushRange=200):
        super().__init__()

        self.image = pygame.Surface([width, height])
        self.image.fill((167, 255, 100))
        self.image.set_colorkey((255, 100, 98))

        pygame.draw.rect(self.image, color, pygame.Rect(0, 0, width, height))

        self.rect = self.image.get_rect()

        # Window constants
        self.screenWidth = screenWidth
        self.screenHeight = screenHeight

        # Player constants
        self.height = height
        self.width = width
        self.moveSpeed = 10
        self.xVelocity = 0
        self.acceleration = 2
        self.deceleration = 3
        self.airResistanceCoeff = 0.01
        self.jumpForce = -15
        self.shortJumpCutoff = 0.3 * self.jumpForce
        self.yVelocity = 0
        self.isJumping = False
        self.jumpKeyHeld = False
        self.push_force = 1000
        self.pull_force = 1000
        self.maxForce = 4
        self.maxPushRange = maxPushRange
        self.mass = 2

        # Spikes
        self.spikes = ["AllomancySteel", None]
        self.steelpushing = False
        self.ironpulling = False

    def moveRight(self):
        if self.xVelocity < 0:  # Decelerate before reversing direction
            self.xVelocity += self.deceleration
        else:  # Accelerate normally
            self.xVelocity = min(
                self.xVelocity + self.acceleration, self.moveSpeed)

    def moveLeft(self):
        if self.xVelocity > 0:  # Decelerate before reversing direction
            self.xVelocity -= self.deceleration
        else:  # Accelerate normally
            self.xVelocity = max(
                self.xVelocity - self.acceleration, -self.moveSpeed)

    def stop(self):
        if not self.isJumping:
            # Gradually reduce velocity to zero
            if self.xVelocity > 0:
                self.xVelocity -= self.deceleration
                if self.xVelocity < 0:  # Stop overshooting zero
                    self.xVelocity = 0
            elif self.xVelocity < 0:
                self.xVelocity += self.deceleration
                if self.xVelocity > 0:  # Stop overshooting zero
                    self.xVelocity = 0

    def jump(self):
        if not self.isJumping:
            self.yVelocity = self.jumpForce
            self.isJumping = True
            self.jumpKeyHeld = True

    def releaseJump(self):
        if self.jumpKeyHeld and self.yVelocity < 0:
            self.yVelocity = max(self.yVelocity, self.shortJumpCutoff)
        self.jumpKeyHeld = False

    def applyForce(self, force_x, force_y):
        # Apply force based on mass
        self.xVelocity += force_x / self.mass
        self.yVelocity += force_y / self.mass

    def steelpush(self, objects):
        for obj in objects:
            if obj.is_metallic:
                # Calculate difference vector between player and object
                dx = obj.rect.centerx - self.rect.centerx
                dy = obj.rect.centery - self.rect.centery
                distance = (dx**2 + dy**2) ** 0.5

                if 0 < distance < self.maxPushRange:
                    direction_x = dx / distance
                    direction_y = dy / distance

                    force_magnitude = self.push_force / distance
                    # Cap the force
                    force_magnitude = min(force_magnitude, self.maxForce)

                    force_x = force_magnitude * direction_x
                    force_y = force_magnitude * direction_y

                    # Apply the force in the opposite direction (push away)
                    self.applyForce(-force_x, -force_y)
                    obj.applyForce(force_x, force_y)

    def ironpull(self, objects):
        for obj in objects:
            if obj.is_metallic:
                # Calculate difference vector between player and object
                dx = obj.rect.centerx - self.rect.centerx
                dy = obj.rect.centery - self.rect.centery
                distance = (dx**2 + dy**2) ** 0.5

                if 0 < distance < self.maxPushRange:
                    # Calculate the direction of the force
                    direction_x = dx / distance
                    direction_y = dy / distance

                    # Distance-based force magnitude
                    force_magnitude = self.pull_force / distance
                    force_magnitude = min(
                        force_magnitude, self.maxForce)  # Cap the force

                    # Apply the force to the object
                    force_x = force_magnitude * direction_x
                    force_y = force_magnitude * direction_y

                    self.applyForce(force_x, force_y)
                    obj.applyForce(-force_x, -force_y)

                    # Smooth out the velocity when the object is close to the player
                    if distance < 10:  # Close enough to reduce speed
                        obj.xVelocity *= 0.8  # Reduce speed gradually when very close
                        obj.yVelocity *= 0.8

                    # Prevent objects from flying into the player or overshooting
                    if self.rect.colliderect(obj.rect):
                        obj.xVelocity = 0  # Stop horizontal movement when in contact
                        obj.yVelocity = 0  # Stop vertical movement when in contact

    def update(self):
        print("x velocity: ", self.xVelocity)
        print("y velocity: ", self.yVelocity)
        # Apply gravity
        self.yVelocity += 1
        # Update horizontal position based on velocity
        self.rect.x += self.xVelocity
        # Update vertical position
        self.rect.y += int(self.yVelocity)

        # Check for collision with ground
        if self.rect.y >= self.screenHeight - self.height:
            self.rect.y = self.screenHeight - self.height
            self.yVelocity = 0
            self.isJumping = False

        # Apply air resistance when in the air (not grounded)
        if not self.isJumping and self.steelpushing:
            self.xVelocity *= 0.9 * (1 / self.mass)  # Friction when grounded
        else:
            # Apply air resistance to horizontal and vertical velocities
            self.xVelocity -= self.xVelocity * self.airResistanceCoeff
            self.yVelocity -= self.yVelocity * self.airResistanceCoeff

        screen_rect = pygame.Rect(0, 0, self.screenWidth, self.screenHeight)
        self.rect.clamp_ip(screen_rect)


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, screenWidth, screenHeight, is_metallic=False, mass=1.0):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill((200, 200, 200) if is_metallic else (100, 100, 100))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.is_metallic = is_metallic

        # Window constants
        self.screenWidth = screenWidth
        self.screenHeight = screenHeight

        # Object physical attributes
        self.height = height
        self.width = width
        self.xVelocity = 0
        self.yVelocity = 0
        self.mass = mass
        self.frictionCoeff = 0.1  # Friction coefficient
        self.maxVelocity = 10

    def applyForce(self, force_x, force_y):
        self.xVelocity += force_x / self.mass
        self.yVelocity += force_y / self.mass

    def update(self):
        # Apply friction to the object's motion
        friction_force_x = -self.xVelocity * self.frictionCoeff * self.mass
        friction_force_y = -self.yVelocity * self.frictionCoeff * self.mass

        # Apply friction to the velocity
        self.applyForce(friction_force_x, friction_force_y)

        # Apply gravity
        self.yVelocity += 1

        # Update horizontal position based on velocity
        self.rect.x += self.xVelocity
        self.rect.y += int(self.yVelocity)

        # Check for collision with ground
        if self.rect.y >= self.screenHeight - self.height:
            self.rect.y = self.screenHeight - self.height
            self.yVelocity = 0
            self.isJumping = False

        screen_rect = pygame.Rect(
            0, 0, self.screenWidth, self.screenHeight)
        self.rect.clamp_ip(screen_rect)
