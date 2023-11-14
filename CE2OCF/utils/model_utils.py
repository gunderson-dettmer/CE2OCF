def _get_annotations(cls, root_class):
    """
    Collect annotations recursively from the class hierarchy up to the root_class.

    Args:
    - cls (type): The class from which to start collecting annotations.
    - root_class (type): The root class up to which annotations should be collected.

    Returns:
    - dict: A merged dictionary of all annotations from cls up to root_class.
    """
    annotations = {}

    # If the class is a subclass of the root class or it's the root class itself
    if issubclass(cls, root_class) or cls is root_class:
        # Get annotations from the current class
        annotations.update(cls.__annotations__)

        # Recursively get annotations from base classes
        for base in cls.__bases__:
            annotations.update(_get_annotations(base, root_class))

    return annotations


def is_iterable(obj, exclude_string=True):
    """
    Check if the given object is iterable.

    Args:
    - obj (Any): The object to check.
    - exclude_string (bool): If True, strings are not considered iterable.

    Returns:
    - bool: True if the object is iterable, False otherwise.
    """
    if exclude_string and isinstance(obj, str):
        return False

    try:
        iter(obj)
        return True
    except TypeError:
        return False
