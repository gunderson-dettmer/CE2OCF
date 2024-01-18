from typing import Any, Callable, Union

from pydantic import BaseModel


class FieldPostProcessorModel(BaseModel):
    # Initialize the attribute for storing field postprocessors at the class level
    _field_postprocessors: dict[str, Callable] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Initialize a separate _field_postprocessors for each subclass - we don't want these registered
        # globally on the parent class
        cls._field_postprocessors = {}

    @classmethod
    def clear_handlers(cls):
        cls._field_postprocessors = {}

    @classmethod
    def register_handlers(cls, handlers: dict[str, Callable]) -> None:
        """
        Register field postprocessors that will be applied after model initialization.

        Parameters:
        -----------
        handlers : Dict[str, Callable]
            A dictionary mapping field names to their respective postprocessing functions.
        """
        for field_name, handler in handlers.items():
            if not callable(handler):
                msg = f"Handler for '{field_name}' must be callable"
                raise TypeError(msg)
            cls._field_postprocessors[field_name] = handler

    @classmethod
    def get_postprocessors(cls) -> dict[str, Callable]:
        return cls._field_postprocessors


class OverridableStringField(BaseModel):
    static: str


class OverridableFloatField(BaseModel):
    static: float


class OverridableBoolField(BaseModel):
    static: bool


class OverridableIntField(BaseModel):
    static: int


class RepeatableDataMap(FieldPostProcessorModel):
    """
    This pattern is to be used where you have some kind of repeated data structure - e.g. stockholders
    where you have multiple repetitions of the same data structure.
    """

    # Sometimes you want to look-up a value on loop 1 and then apply its value to all iterations.
    # Put name of such variables here.
    repeated_variables: Union[str, list[str], OverridableStringField, list[OverridableStringField]]
    repeat_count: Union[str, OverridableStringField, OverridableIntField]
    repeated_pattern: Union[dict[str, Any], BaseModel, str, FieldPostProcessorModel]
