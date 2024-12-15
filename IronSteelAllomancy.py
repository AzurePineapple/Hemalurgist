from dataclasses import dataclass


@dataclass
class IronSteelAllomancy:
    chargePower: float = 1/8
    wallOcclusionFactor: float = 3/4
    distanceConstant = 100  # Lower values mean faster allomantic force falloff with distance
    allomanticConstant = 100
    velocityConstant = 100
