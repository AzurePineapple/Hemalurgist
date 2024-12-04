import math
import pygame

# Define some debugging globals that will become settings later
EASY_FERUCHEMY = True


class PlayerSprite(pygame.sprite.Sprite):
    def __init__(self, color, height, width, screenWidth, screenHeight, maxPushRange=300):
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
        self.aerialMoveSpeedLimit = 20
        self.xVelocity = 0
        self.airResistanceCoeff = 0.01
        self.jumpForce = -15
        self.shortJumpCutoff = 0.3 * self.jumpForce
        self.yVelocity = 0
        self.isAirborne = False
        self.jumpKeyHeld = False
        self.push_force = 1000
        self.pull_force = 1000
        self.maxForce = 4
        self.maxPushRange = maxPushRange
        self.coneAngle = 45

        # Spikes
        self.spikes = ["AllomancySteel", None]

        # Allomancy flags - False for not burning, True if burning
        self.aSteel = False
        self.aIron = False
        self.aAluminium = False
        self.aBendalloy = False
        self.aCadmium = False
        self.aBrass = False
        self.aZinc = False
        self.aChromium = False
        self.aCopper = False
        self.aDuralumin = False
        self.aTin = False

        # Feruchemy flags - +1 indicates filling at 1st stage rate (value tbd), -3 means tapping at 3rd stage rate etc.
        self.fIron = 0
        self.fSteel = 0
        self.fPewter = 0
        self.fGold = 0
        self.fBrass = 0
        self.fChromium = 0

        self.feruchemyChangeRate = 3
        self.metalMindCapacity = 5000

        # Metalminds
        self.ironMetalMind = 0
        self.steelMetalMind = 0
        self.pewterMetalMind = 0
        self.goldMetalMind = 0
        self.brassMetalMind = 0
        self.chromiumMetalMind = 0

        # All feruchemy related attributes

        # Iron
        self.mass = self.baseMass = 2
        # Steel
        self.moveSpeedLimit = self.baseMoveSpeedLimit = 10
        self.acceleration = self.moveSpeedLimit / 5
        self.deceleration = self.moveSpeedLimit / 5
        # Pewter
        self.strength = self.baseStrength = 5
        # Gold
        self.health = self.baseHealth = 100
        # Brass
        self.warmth = self.baseWarmth = 50
        # Chromium
        self.fortune = self.baseFortune = 100

    def moveRight(self):
        accelerationValue = self.acceleration if not self.isAirborne else self.acceleration/2
        if self.xVelocity < 0:  # Decelerate before reversing direction
            self.xVelocity += self.deceleration
        else:  # Accelerate normally
            self.xVelocity = min(
                self.xVelocity + accelerationValue, self.moveSpeedLimit)

    def moveLeft(self):
        accelerationValue = self.acceleration if not self.isAirborne else self.acceleration/2
        if self.xVelocity > 0:  # Decelerate before reversing direction
            self.xVelocity -= self.deceleration
        else:  # Accelerate normally
            self.xVelocity = max(
                self.xVelocity - accelerationValue, -self.moveSpeedLimit)

    def stop(self):
        if not self.isAirborne:
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
        if not self.isAirborne:
            self.yVelocity = self.jumpForce
            self.isAirborne = True
            self.jumpKeyHeld = True

    def releaseJump(self):
        if self.jumpKeyHeld and self.yVelocity < 0:
            self.yVelocity = max(self.yVelocity, self.shortJumpCutoff)
        self.jumpKeyHeld = False

    def createAimingCone(self, screenWidth, screenHeight):
        # Create surface for the cone
        coneSurface = pygame.Surface(
            (screenWidth, screenHeight), pygame.SRCALPHA)

        # Get and normalise the direction vector to the mouse
        playerPos = self.rect.center
        mousePos = pygame.mouse.get_pos()
        mouseDir = (mousePos[0] - playerPos[0], mousePos[1]-playerPos[1])
        mag = (mouseDir[0]**2 + mouseDir[1]**2)**0.5
        if mag > 0:
            mouseDir = (mouseDir[0]/mag, mouseDir[1]/mag)

        # Calculate the boundary angles
        baseAngle = math.atan2(mouseDir[1], mouseDir[0])
        coneAngleRad = math.radians(self.coneAngle / 2)

        # Define start and end angles
        startAngle = baseAngle - coneAngleRad
        endAngle = baseAngle + coneAngleRad

        # Fill the cone slice
        points = [playerPos]
        steps = 20
        for i in range(steps+1):
            angle = startAngle + i * (endAngle-startAngle)/steps
            x = int(playerPos[0] + self.maxPushRange*math.cos(angle))
            y = int(playerPos[1] + self.maxPushRange*math.sin(angle))
            points.append((x, y))

        pygame.draw.polygon(coneSurface, (100, 100, 255, 10), points)
        return coneSurface

    def objectInRange(self, obj):
        # Calculate vector to the object
        dx = obj.rect.centerx - self.rect.centerx
        dy = obj.rect.centery - self.rect.centery
        distance = (dx**2 + dy**2) ** 0.5

        # Normalise the vector
        if distance > 0:
            dx /= distance
            dy /= distance

        if 0 < distance <= self.maxPushRange:
            return True, (dx, dy), distance
        else:
            return False, (dx, dy), distance

    def objectInTargettingCone(self, objVector):
        """Returns true if vector to an object lies within the targetting cone of the player, which is projected from the player to the mouse cursor

        Args:
            objVector (tuple): contains the x and y elements of the vector pointing from the player to the object (normalised)
        """
        # Get vector from player to mouse and normalise it
        mousePos = pygame.mouse.get_pos()
        mouseDir = (mousePos[0] - self.rect.center[0],
                    mousePos[1] - self.rect.center[1])
        mag = (mouseDir[0]**2 + mouseDir[1]**2)**0.5
        if mag > 0:
            mouseDir = (mouseDir[0]/mag, mouseDir[1]/mag)

        # Calculate the angle between the normalised vectors and convert to degrees
        dotProduct = objVector[0] * mouseDir[0] + objVector[1] * mouseDir[1]
        # Clamp the value of the dot product so that it cannot go out of domain for arccos function (caused by floating point math errors)
        dotProduct = min(max(dotProduct, 0), 1)
        try:
            angle = math.acos(dotProduct) * (180 / math.pi)
        except ValueError:
            raise Exception("dotProduct out of range of arccos function, value was: " +
                            str(dotProduct))

        # Return true if angle falls within the size of the cone
        return angle <= self.coneAngle/2

    def applyForce(self, force_x, force_y):
        # Apply force based on mass
        self.xVelocity += force_x / self.mass
        self.yVelocity += force_y / self.mass

    def steelpush(self, objects):
        for obj in objects:
            if obj.is_metallic:

                inRange, vector, distance = self.objectInRange(obj)
                aimedAt = self.objectInTargettingCone(vector)

                if inRange and aimedAt:
                    forceMag = self.push_force / distance
                    forceMag = min(forceMag, self.maxForce)

                    forceX = forceMag * vector[0]
                    forceY = forceMag * vector[1]

                    self.applyForce(-forceX, -forceY)
                    obj.applyForce(forceX, forceY)

    def ironpull(self, objects):
        for obj in objects:
            if obj.is_metallic:

                inRange, vector, distance = self.objectInRange(obj)
                aimedAt = self.objectInTargettingCone(vector)
                if inRange and aimedAt:
                    forceMag = self.push_force / distance
                    forceMag = min(forceMag, self.maxForce)

                    forceX = forceMag * vector[0]
                    forceY = forceMag * vector[1]

                    self.applyForce(forceX, forceY)
                    obj.applyForce(-forceX, -forceY)

                    # Smooth out the velocity when the object is close to the player
                    if distance < 10:  # Close enough to reduce speed
                        obj.xVelocity *= 0.8  # Reduce speed gradually when very close
                        obj.yVelocity *= 0.8

                    # Prevent objects from flying into the player or overshooting
                    if self.rect.colliderect(obj.rect):
                        obj.xVelocity = 0  # Stop horizontal movement when in contact
                        obj.yVelocity = 0  # Stop vertical movement when in contact

    def changeMetalmindRate(self, metal, change):

        match metal:
            case "iron":
                self.fIron += change

            case _:
                print("Invalid metal passed")

    def limitFeruchemy(self):
        """constrains values relevant to feruchemy to value ranges
        """

        # Constrains the value of each metals fill/tap rate to lie within range -3 to +3
        self.fIron = min(max(self.fIron, -3), 3)
        self.fSteel = min(max(self.fSteel, -3), 3)
        self.fPewter = min(max(self.fPewter, -3), 3)
        self.fGold = min(max(self.fGold, -3), 3)
        self.fBrass = min(max(self.fBrass, -3), 3)
        self.fChromium = min(max(self.fChromium, -3), 3)

        # Constrains the amount of attribute stored in each metalmind
        self.ironMetalMind = min(
            max(self.ironMetalMind, 0), self.metalMindCapacity)
        self.steelMetalMind = min(
            max(self.steelMetalMind, 0), self.metalMindCapacity)
        self.pewterMetalMind = min(
            max(self.pewterMetalMind, 0), self.metalMindCapacity)
        self.goldMetalMind = min(
            max(self.goldMetalMind, 0), self.metalMindCapacity)
        self.brassMetalMind = min(
            max(self.brassMetalMind, 0), self.metalMindCapacity)
        self.chromiumMetalMind = min(
            max(self.chromiumMetalMind, 0), self.metalMindCapacity)

    def changeAttributes(self):
        """Alters feruchemical attributes when the player is tapping/filling a metalmind
        """
        # Iron

        match self.fIron:
            case -3:
                self.mass = 0.25 * self.baseMass
            case -2:
                self.mass = 0.5 * self.baseMass
            case -1:
                self.mass = 0.75 * self.baseMass
            case 0:
                self.mass = self.baseMass
            case 1:
                self.mass = 2 * self.baseMass
            case 2:
                self.mass = 3 * self.baseMass
            case 3:
                self.mass = 10 * self.baseMass

    def updateFeruchemy(self):

        # If metalminds are full or empty and player tried to fill/tap respectively, set the stage to 0
        if self.ironMetalMind >= self.metalMindCapacity and self.fIron < 0:
            self.fIron = 0
        elif self.ironMetalMind <= 0 and self.fIron > 0:
            self.fIron = 0

        self.changeAttributes()
        self.ironMetalMind += self.baseMass - self.mass

        # Sanity check all metalmind values
        self.limitFeruchemy()

    def update(self):

        # Check if player is airborne and ensure flag is set correctly
        self.isAirborne = False if self.rect.y >= self.screenHeight - self.height else True
        # Apply gravity
        self.yVelocity += 1

        # Ensure player is not moving faster than move speed limit
        if self.xVelocity < 0:
            self.xVelocity = max(self.xVelocity, -self.moveSpeedLimit)
        elif self.xVelocity > 0:
            self.xVelocity = min(self.xVelocity, self.moveSpeedLimit)
        if self.yVelocity < 0:
            self.yVelocity = max(self.yVelocity, -self.aerialMoveSpeedLimit)
        elif self.yVelocity > 0:
            self.yVelocity = min(self.yVelocity, self.aerialMoveSpeedLimit)

        # Update horizontal position based on velocity
        self.rect.x += int(self.xVelocity)
        # Update vertical position
        self.rect.y += int(self.yVelocity)

        # Check for collision with ground
        if self.rect.y >= self.screenHeight - self.height:
            self.rect.y = self.screenHeight - self.height
            self.yVelocity = 0
            self.isAirborne = False

        # Apply friction when grounded and pushing
        if not self.isAirborne and self.aSteel:
            self.xVelocity *= 0.9 * (1 / self.mass)  # Friction when grounded
        else:
            # Apply air resistance to horizontal and vertical velocities
            self.xVelocity -= self.xVelocity * self.airResistanceCoeff
            self.yVelocity -= self.yVelocity * self.airResistanceCoeff

        screen_rect = pygame.Rect(0, 0, self.screenWidth, self.screenHeight)
        self.rect.clamp_ip(screen_rect)

        # Do feruchemy updates
        self.updateFeruchemy()


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, screenWidth, screenHeight, is_metallic=False, mass=1.0, suspended=False):
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
        self.suspended = suspended

    def applyForce(self, force_x, force_y):
        if not self.suspended:
            self.xVelocity += force_x / self.mass
            self.yVelocity += force_y / self.mass

    def update(self):
        # Apply friction to the object's motion
        friction_force_x = -self.xVelocity * self.frictionCoeff * self.mass
        friction_force_y = -self.yVelocity * self.frictionCoeff * self.mass

        # Apply friction to the velocity
        self.applyForce(friction_force_x, friction_force_y)

        # Apply gravity
        if not self.suspended:
            self.yVelocity += 1

        # Update horizontal position based on velocity
        self.rect.x += int(self.xVelocity)
        self.rect.y += int(self.yVelocity)

        # Check for collision with ground
        if self.rect.y >= self.screenHeight - self.height:
            self.rect.y = self.screenHeight - self.height
            self.yVelocity = 0
            self.isAirborne = False

        screen_rect = pygame.Rect(
            0, 0, self.screenWidth, self.screenHeight)
        self.rect.clamp_ip(screen_rect)
