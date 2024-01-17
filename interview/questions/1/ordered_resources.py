# Copyright (c) 2021. Syntax Cloud Systems, LLC - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential

"""Module defining the `OrderedResources` class."""

import random
from typing import List

import rich


class NegativeSize(ValueError):
    """Raised when trying to use a negative size."""

    def __str__(self):
        """Human-readable error message."""
        return "Negative sizes are not valid!"


class IndexOutOfBound(ValueError):
    """Raised when trying to access a resource which does not exists."""

    def __str__(self):
        """Human-readable error message."""
        return "Tried to access a resource which does not exists."


class TooManyProbes(RuntimeError):
    """Raised when probing free resources for the third time."""


class AllResourcesInUse(Exception):
    """Raised when all resources are in use."""


    def __str__(self):
        """Human-readable error message."""
        return "Tried to probe free resources too many times."


class OrderedResources:
    """Pool of resources indexed from `0` to `self.size - 1`."""

    def __init__(self, size: int):
        """
        Instantiate a new `OrderedResources`.

        The first `N` resources will be busy where `N` in a random integer
        between `0` and `size`.

        # Warning

        Protected state may not be accessed by the `locate` method.
        """
        if size < 0:
            raise NegativeSize()

        self.size = size

        self._free_count = 0
        self._busy_count = 0
        self._first_available_resource = random.randint(0, self.size - 1)

    def is_resource_free(self, index: int) -> bool:
        """
        Return `True` if and only if the indexed resource is available.

        This stub is constant time, the production version exhibit the
        following runtime-behavior:

        * Checking the state of a busy resource is an expansive operation.

        * Checking the state of a free resource is an order of magnitude more
          expansive.

        Using this method more than twice on a free resource would disrupt
        production.
        """
        if index >= self.size:
            raise IndexOutOfBound()

        is_free = index >= self._first_available_resource

        if is_free:
            self._free_count += 1

            print(self._free_count)
            if self._free_count > 2:
                raise TooManyProbes()
        else:
            self._busy_count += 1

        return is_free

    def locate(self) -> int:
        if self.size == 0:
            raise AllResourcesInUse()

        # Cache to store the results of is_resource_free
        cache = {}
        free_resource_found = False

        for i in range(self.size):
            if i not in cache:
                cache[i] = self.is_resource_free(i)

            if cache[i]:
                if free_resource_found:
                    # Second free resource found, return the previous one
                    return i - 1
                free_resource_found = True
            else:
                # Reset the flag if a busy resource is found after a free one
                free_resource_found = False

        if free_resource_found:
            # The last resource is free
            return self.size - 1

        raise AllResourcesInUse()

        raise NotImplementedError("Please implement this method.")


# pylint: disable=protected-access,invalid-name


if __name__ == "__main__":
    POOL_SIZE = 100
    ITERATIONS = 100

    sample: List[int] = []
    correctness = True

    for _ in range(0, ITERATIONS):
        pool = OrderedResources(POOL_SIZE)

        try:
            next_free = pool.locate()
        except NotImplementedError:
            raise
        except Exception:  # pylint: disable=broad-except
            if pool.size != pool._first_available_resource:
                correctness = False
        else:
            if pool.size == pool._first_available_resource:
                correctness = False

            if next_free != pool._first_available_resource:
                correctness = False

        sample.append(pool._busy_count + pool._free_count)

    if not sample:
        rich.print(
            {
                "minimum": 0,
                "maximum": 0,
                "average": 0.0,
                "correctness": correctness,
            }
        )
    else:
        rich.print(
            {
                "minimum": min(sample),
                "maximum": max(sample),
                "average": sum(sample) / len(sample),
                "correctness": correctness,
            }
        )
