import numpy as np
import numpy.typing as npt


def clampMagnitude(vector: npt.NDArray, maxMagnitude: float):
    magnitude = np.linalg.norm(vector)
    if magnitude > maxMagnitude:
        return (vector/magnitude) * maxMagnitude
    return vector


def vectorProject(vector: npt.NDArray, direction: npt.NDArray):
    # Equivalent to direction**2 for magnitude squared
    direction_norm_squared = np.dot(direction, direction)
    if direction_norm_squared == 0:
        # Return a zero vector if direction is zero
        return np.zeros_like(vector)
    return (np.dot(vector, direction) / direction_norm_squared) * direction
