import typing


class OcfEventGeneratorFunctionSig(typing.Protocol):
    """
    This is a typing-related signature function definition describing a callable (function) you can pass into the
    vesting schedule generators to customize the type of vesting condition that's generated. You obviously can make use
    of these inputs however you like (including generating weird double triggers that would give you months of
    vesting credit depending on when the double trigger occurs), but these seem like the requisite inputs.
    """

    def __call__(
        self,
        period_number: int = 0,
        period_type: str = "MONTHS",
        on_or_after_fully_vested_cutoff: bool = False,
        portion_numerator: int = 0,
        portion_denominator: int = 0,
        id: str = "",
        **kwargs,
    ) -> dict:
        ...
