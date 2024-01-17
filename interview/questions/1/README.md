# Context

The class `OrderedResources` defined in `ordered_resources.py` is an
abstraction around an ordered resource pool which can be of any size.

Each resource is assigned an integer index starting at `0` up to `size - 1`.

Resources are acquired in orders; meaning that if resource `i` is in use, it
implies all resources `j <= i` are also in use.

The method `OrderedResources.is_resource_free(self, index: int) -> bool` may be
used to check if a specific resource if free. However, it is a very expansive
operation. Even more so if the resource is actually free (i.e. the method
returns `True`).

The class and supporting methods are fully implemented and documented.

# Requirements

You are tasked to implement a new method called `locate(self) -> int` on the
class `OrderedResources` with the following contract:

* It must find the resource with the lowest index which is available using
  `OrderedResources.is_resource_free`.

* Due to performance constraints, the use of
  `OrderedResources.is_resource_free` is forbidden after it returned `True` for
  the second time (i.e. you must have the index of the next free available
  resource figured out at that point).

* `locate` must still make an effort to minimize the number of calls to
  `OrderedResources.is_resource_free` even when it returns `False`.

* `locate` must raise an exception if all resources are in use.

# Testing

Running the `ordered_resources.py` as a script will run a simulation which will
test your implementation of `locate` and give you some performance metrics (on
top of letting you know if your solution is actually correct).

# Simplifying Assumption

You may assume that the state of the resources does not change while `locate`
is executing.
