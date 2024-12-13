from dataclasses import dataclass


@dataclass
class IronSteelAllomancy:
    chargePower: float = 1/8
    wallOcclusionFactor: float = 3/4
    distanceConstant = 100
    allomanticConstant = 1000
    velocityConstant = 100
