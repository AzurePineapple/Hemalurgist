import math
import numpy as np
import numpy.typing as npt
import pygame
from IronSteelAllomancy import IronSteelAllomancy
import functions

# Define some debugging globals that will become settings later
EASY_FERUCHEMY = True
GRAVITYCONSTANT = 1


class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, height, width, screenWidth, screenHeight, perfectlyAnchored):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill((167, 255, 100))
        self.image.set_colorkey((255, 100, 98))

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        # Window constants
        self.screenWidth = screenWidth
        self.screenHeight = screenHeight

        # Physical constants
        self.mass = int
        self.velocity = np.array([0.0, 0.0])

        self.height = height
        self.width = width
        self.isPerfectlyAnchored = perfectlyAnchored
        self.isAirborne = False
        self.deceleration = 1
        self.frictionCoeff = 0.1  # Friction coefficient
        self.dragCoeff = 0.1

        self.netForceThisFrame = np.array([0.0, 0.0])

    def addForce(self, force: npt.NDArray):
        if not self.isPerfectlyAnchored:
            self.netForceThisFrame += force

    def applyForce(self):
        # Apply force based on mass
        if not self.isPerfectlyAnchored:
            self.velocity += self.netForceThisFrame / self.mass

    def applyGravity(self):
        if not self.isPerfectlyAnchored:
            self.velocity[1] += GRAVITYCONSTANT

    def updatePosition(self):
        """Updates the sprites position based on its velocity
        """
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]

    def getCentreOfMassArray(self):
        return np.array([self.rect.centerx, self.rect.centery])

    def stopFallingAtGround(self):
        # Check for collision with ground
        if self.rect.y >= self.screenHeight - self.height:
            self.rect.y = self.screenHeight - self.height
            self.velocity[1] = 0
            self.isAirborne = False

    def stop(self):
        if not self.isAirborne:
            # Gradually reduce velocity to zero
            if self.velocity[0] > 0:
                self.velocity[0] -= self.deceleration
                if self.velocity[0] < 0:  # Stop overshooting zero
                    self.velocity[0] = 0
            elif self.velocity[0] < 0:
                self.velocity[0] += self.deceleration
                if self.velocity[0] > 0:  # Stop overshooting zero
                    self.velocity[0] = 0

    def addFriction(self):
        # Apply friction to the object's motion
        if not self.isAirborne:
            friction_force_x = - \
                self.velocity[0] * self.frictionCoeff * self.mass

            frictionForce = np.array([friction_force_x, 0])
            
            # Apply friction to the velocity
            self.addForce(frictionForce)
        else:
            # Apply air resistance to horizontal and vertical velocities
            if not np.allclose(self.velocity, 0.0):
                dragForce = -1*self.dragCoeff * \
                    np.linalg.norm(self.velocity)**2 * \
                    (self.velocity/np.linalg.norm(self.velocity))

                self.addForce(dragForce)


class Object(Entity):
    def __init__(self, x, y, width, height, screenWidth, screenHeight, is_metallic=False, mass=1.0, perfectlyAnchored=False):
        Entity.__init__(self, x, y, height, width, screenWidth,
                        screenHeight, perfectlyAnchored)
        self.image = pygame.Surface([width, height])
        self.image.fill((200, 200, 200) if is_metallic else (100, 100, 100))
        self.is_metallic = is_metallic

        # Window constants
        self.screenWidth = screenWidth
        self.screenHeight = screenHeight

        self.mass = mass
        self.magneticMass = mass
        self.maxVelocity = 10
        self.charge = math.pow(
            self.magneticMass, IronSteelAllomancy.chargePower)
        self.lastWasPushed = False

    def update(self):

        self.addFriction()
        self.applyForce()  # Applies all added forces to the velocity
        self.applyGravity()  # Applies acceleration due to gravity to the velocity
        self.updatePosition()  # Updates the positon according to the velocity
        self.stopFallingAtGround()

        # Clear force this frame
        self.netForceThisFrame *= 0

        screen_rect = pygame.Rect(
            0, 0, self.screenWidth, self.screenHeight)
        self.rect.clamp_ip(screen_rect)


class PlayerSprite(Entity):
    def __init__(self, x, y, color, height, width, screenWidth, screenHeight, maxPushRange=500):
        Entity.__init__(self, x, y, height, width,
                        screenWidth, screenHeight, False)

        pygame.draw.rect(self.image, color, pygame.Rect(0, 0, width, height))

        # Player constants

        self.aerialMoveSpeedLimit = 30
        self.jumpForce = -1000
        self.shortJumpCutoff = 0.3 * self.jumpForce

        self.jumpKeyHeld = False
        self.push_force = 1000
        self.pull_force = 1000
        self.maxForce = 4
        self.maxPushRange = maxPushRange
        self.coneAngle = 45

        # Spikes
        self.spikes = ["AllomancySteel", None]

        # Feruchemy

        self.feruchemicalMetals = ["steel", "iron",
                                   "pewter", "gold",
                                   "brass", "chromium"]

        # Feruchemy flags - +1 indicates filling at 1st stage rate (value tbd), -3 means tapping at 3rd stage rate etc.
        self.feruchemyFlags = {"iron": 0, "steel": 0,
                               "pewter": 0, "gold": 0,
                               "brass": 0, "chromium": 0}

        self.feruchemyChangeRate = 3
        self.metalMindCapacity = 5000

        # Metalminds
        self.metalMinds = {"iron": 0, "steel": 0,
                           "pewter": 0, "gold": 0,
                           "brass": 0, "chromium": 0}

        # All feruchemy related attributes

        # Iron
        self.mass = self.baseMass = 20
        # Steel
        self.moveSpeedLimit = self.baseMoveSpeedLimit = 10
        self.acceleration = self.baseAcceleration = self.moveSpeedLimit / 5
        self.deceleration = self.baseDeceleration = self.moveSpeedLimit / 5
        # Pewter
        self.strength = self.baseStrength = 5
        # Gold
        self.health = self.baseHealth = 100
        # Brass
        self.warmth = self.baseWarmth = 50
        # Chromium
        self.fortune = self.baseFortune = 100

        self.allomanticMetals = ["steel", "iron", "aluminium", "bendalloy",
                                 "cadmium", "brass", "zinc", "chromium", "duralumin", "zinc"]

        # Allomancy

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

        self.allomanticStrength = 1
        self.charge = math.pow(
            self.mass, IronSteelAllomancy.chargePower)

    def moveRight(self):
        accelerationValue = self.acceleration if not self.isAirborne else self.acceleration/2
        if self.velocity[0] < 0:  # Decelerate before reversing direction
            self.velocity[0] += self.deceleration
        else:  # Accelerate normally
            self.velocity[0] = min(
                self.velocity[0] + accelerationValue, self.moveSpeedLimit)

    def moveLeft(self):
        accelerationValue = self.acceleration if not self.isAirborne else self.acceleration/2
        if self.velocity[0] > 0:  # Decelerate before reversing direction
            self.velocity[0] -= self.deceleration
        else:  # Accelerate normally
            self.velocity[0] = max(
                self.velocity[0] - accelerationValue, -self.moveSpeedLimit)

    def jump(self):
        if not self.isAirborne:
            # self.velocity[1] = self.jumpForce

            self.addForce(np.array([0, self.jumpForce]))
            self.isAirborne = True
            self.jumpKeyHeld = True

    def releaseJump(self):
        if self.jumpKeyHeld and self.velocity[1] < 0:
            self.velocity[1] = max(self.velocity[1], self.shortJumpCutoff)
        self.jumpKeyHeld = False

    def clampVelocity(self):
        # Ensure player is not moving faster than move speed limit
        if self.velocity[0] < 0:
            self.velocity[0] = max(self.velocity[0], -self.moveSpeedLimit)
        elif self.velocity[0] > 0:
            self.velocity[0] = min(self.velocity[0], self.moveSpeedLimit)
        if self.velocity[1] < 0:
            self.velocity[1] = max(
                self.velocity[1], -self.aerialMoveSpeedLimit)
        elif self.velocity[1] > 0:
            self.velocity[1] = min(self.velocity[1], self.aerialMoveSpeedLimit)

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

        pygame.draw.polygon(coneSurface, (100, 100, 255, 50), points)
        return coneSurface

    def objectInRange(self, obj: Object):
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

    def isValidTarget(self, obj: Object) -> bool:
        inRange, vector, distance = self.objectInRange(obj)
        aimedAt = self.objectInTargettingCone(vector)

        return inRange and aimedAt and obj.is_metallic

    def calculateAllomanticForce(self, obj: Object) -> npt.NDArray:
        """Calculates the allomantic force between the allomancer (self) and the object being targetted
            F = A * S * C * d 

            F: Allomantic Force
     *      A: Allomantic Constant (~1000, subject to change)
     *      S: Allomantic Strength (1), a constant, different for each Allomancer
     *      C: Allomantic Charge (8th root of (Allomancer mass * target mass)), different for each Allomancer-target pair.
     *          Is the effect of mass on the force.
     *      d: Distance factor (between 0% and 100%)
     *          Is the effect of the distance between the target and Allomancer on the force.


        Args:
            obj (_type_): _description_
        """

        # Calculate vector to the object
        positionDifference = obj.getCentreOfMassArray() - self.getCentreOfMassArray()

        if np.allclose(positionDifference, 0.0):
            positionDifference = np.array([0.0, -0.0001, 0.0])

        magnitude = np.linalg.norm(positionDifference)
        positionDifferenceNorm = positionDifference / \
            magnitude if magnitude > 0 else positionDifference

        distanceFactor = positionDifferenceNorm * \
            np.exp(-magnitude/IronSteelAllomancy.distanceConstant)

        force = IronSteelAllomancy.allomanticConstant * \
            self.allomanticStrength * self.charge * obj.charge * distanceFactor

        return force

    def calculateForce(self, obj: Object, pushing: bool):
        """Calculates the net force between allomancer and the object using the formula N = F + B
        where N is the net force exerted on the allomancer and the object, F is the calculated 
        allomantic force, and B is a bonus push boost coming from an anchored object

        Args:
            obj (_type_): _description_
        """

        # Steps:
        # 1. Calculate allomantic force exerted on target, producing F
        # 2. Scale the force with a factor exponential with the relative velocity of the two entities producing restitution force
        # 3. Sum the allomantic force and the restitution force from the object and apply to allomancer
        # 4. Sum the allomantic force and the restitution force from the allomancer and apply to the object

        obj.lastWasPushed = pushing

        allomanticForce = self.calculateAllomanticForce(obj)
        # print(np.linalg.norm(allomanticForce))
        direction = allomanticForce / np.linalg.norm(allomanticForce)

        # Flip direction of force for pulling
        if self.aSteel and not self.aIron:
            allomanticForce *= -1
        elif self.aSteel and self.aIron:  # If pushing and pulling on the same object, net zero force is exerted on the object
            allomanticForce *= 0

        # Ensure force does not exceed maximum (don't know what we're doing with this yet so womp womp set it to a mill)
        allomanticForce = functions.clampMagnitude(allomanticForce, 1_000_000)

        relativeVelocity = functions.vectorProject(
            obj.velocity-self.velocity, direction)
        velocityFactor = 1 - \
            np.exp(-np.linalg.norm(relativeVelocity) /
                   IronSteelAllomancy.velocityConstant)

        # Adds the "symmetrical" model from Invested by austin j taylor, should mean that pushes are weaker when object is moving away from allomancer, and vice versa
        if np.dot(relativeVelocity, direction) > 0:
            velocityFactor *= -1

        # Calculate the anchored push boost
        restitutionForceFromAllomancer = allomanticForce * velocityFactor
        restitutionForceFromObj = allomanticForce * - velocityFactor

        # Calculate the total force on the allomancer and the object
        netForceOnAllomancer = allomanticForce + restitutionForceFromObj
        netForceonObject = -allomanticForce + restitutionForceFromAllomancer

        # Add the force to this frames force
        self.netForceThisFrame += netForceOnAllomancer
        obj.netForceThisFrame += netForceonObject

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

                    force = np.array([forceX, forceY])

                    self.addForce(-force)
                    obj.addForce(force)

    def ironpull(self, objects):
        for obj in objects:
            if obj.is_metallic:

                inRange, vector, distance = self.objectInRange(obj)
                aimedAt = self.objectInTargettingCone(vector)
                if inRange and aimedAt:
                    forceMag = self.pull_force / distance
                    forceMag = min(forceMag, self.maxForce)

                    forceX = forceMag * vector[0]
                    forceY = forceMag * vector[1]

                    force = np.array([forceX, forceY])
                    print(force)
                    self.addForce(force)
                    obj.addForce(-force)

                    # Smooth out the velocity when the object is close to the player
                    if distance < 10:  # Close enough to reduce speed
                        obj.xVelocity *= 0.8  # Reduce speed gradually when very close
                        obj.yVelocity *= 0.8

                    # Prevent objects from flying into the player or overshooting
                    if self.rect.colliderect(obj.rect):
                        obj.xVelocity = 0  # Stop horizontal movement when in contact
                        obj.yVelocity = 0  # Stop vertical movement when in contact

    def changeMetalmindRate(self, metal, change):

        if not metal in self.feruchemicalMetals:
            raise Exception(
                "Passed metal not in available feruchemical metals")
        else:
            self.feruchemyFlags[metal] += change

    def limitFeruchemy(self):
        """constrains values relevant to feruchemy to value ranges
        """

        # Constrains the value of each metals fill/tap rate to lie within range -3 to +3
        for metal in self.feruchemicalMetals:
            self.feruchemyFlags[metal] = min(
                max(self.feruchemyFlags[metal], -3), 3)

        # Constrains the amount of attribute stored in each metalmind
        for metal in self.feruchemicalMetals:
            self.metalMinds[metal] = min(
                max(self.metalMinds[metal], 0), self.metalMindCapacity)

    def changeAttributes(self):
        """Alters feruchemical attributes when the player is tapping/filling a metalmind
        """
        # Iron

        match self.feruchemyFlags["iron"]:
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

        match self.feruchemyFlags["steel"]:
            case -3:
                self.moveSpeedLimit = 0.25 * self.baseMoveSpeedLimit
                self.acceleration = 0.25 * self.baseAcceleration
                self.deceleration = 0.25 * self.baseDeceleration
            case -2:
                self.moveSpeedLimit = 0.5 * self.baseMoveSpeedLimit
                self.acceleration = 0.5 * self.baseAcceleration
                self.deceleration = 0.5 * self.baseDeceleration
            case -1:
                self.moveSpeedLimit = 0.75 * self.baseMoveSpeedLimit
                self.acceleration = 0.75 * self.baseAcceleration
                self.deceleration = 0.75 * self.baseDeceleration
            case 0:
                self.moveSpeedLimit = self.baseMoveSpeedLimit
                self.acceleration = self.baseAcceleration
                self.deceleration = self.baseDeceleration
            case 1:
                self.moveSpeedLimit = 2 * self.baseMoveSpeedLimit
                self.acceleration = 2 * self.baseAcceleration
                self.deceleration = 2 * self.baseDeceleration
            case 2:
                self.moveSpeedLimit = 3 * self.baseMoveSpeedLimit
                self.acceleration = 3 * self.baseAcceleration
                self.deceleration = 3 * self.baseDeceleration
            case 3:
                self.moveSpeedLimit = 10 * self.baseMoveSpeedLimit
                self.acceleration = 10 * self.baseAcceleration
                self.deceleration = 10 * self.baseDeceleration

    def updateFeruchemy(self):

        # If metalminds are full or empty and player tried to fill/tap respectively, set the stage to 0
        for metal in self.feruchemicalMetals:
            # If metalmind is over capacity and trying to fill, stop filling
            if self.metalMinds[metal] >= self.metalMindCapacity and self.feruchemyFlags[metal] < 0:
                self.feruchemyFlags[metal] = 0
            # Else if metalmind is empty and trying to drain, stop draining
            elif self.metalMinds[metal] <= 0 and self.feruchemyFlags[metal] > 0:
                self.feruchemyFlags[metal] = 0

        self.changeAttributes()
        self.metalMinds["iron"] += int(self.baseMass - self.mass)
        self.metalMinds["steel"] += int(self.baseMoveSpeedLimit -
                                        self.moveSpeedLimit)

        # Sanity check all metalmind values
        self.limitFeruchemy()

    def update(self):
        # Check if player is airborne and ensure flag is set correctly
        self.isAirborne = False if self.rect.y >= self.screenHeight - self.height else True

        # Apply various forces

        self.addFriction()
        self.applyForce()
        self.applyGravity()
        self.clampVelocity()
        self.updatePosition()

        self.stopFallingAtGround()

        screen_rect = pygame.Rect(0, 0, self.screenWidth, self.screenHeight)
        # self.rect.clamp_ip(screen_rect)

        # Do feruchemy updates
        self.updateFeruchemy()

        # if self.netForceThisFrame.all() != np.array([0.0, 0.0]).all():
        # print(self.netForceThisFrame)

        # Clear force this frame
        self.netForceThisFrame *= 0

    def isPushPulling(self):
        return self.aSteel or self.aIron
