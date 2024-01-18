from __future__ import annotations

import itertools
import random
import xml.etree.ElementTree as ET  # noqa

from CE2OCF.ce.transforms.json import (
    convert_ce_answers_xml_to_json_string,
)
from CE2OCF.ce.transforms.xml import (
    convert_pydantic_to_xml_elem,
    xml_elements_to_ce_xml_tree,
)
from CE2OCF.ocf.mocks.company import mock_company
from CE2OCF.ocf.mocks.officers import mock_director
from CE2OCF.ocf.mocks.stockholders import mock_stockholder, sum_shares
from CE2OCF.ocf.postprocessors import (
    GD_HUMAN_REPEAT_SELECTIONS_TO_VAR_NAMES,
)
from CE2OCF.types.enums import RepeatableFields, TransferRestrictionEnum
from CE2OCF.types.models import (
    BylawVars,
    Company,
    Director,
    FormVars,
    Stockholder,
)
from CE2OCF.utils.log_utils import logger


def mock_formvars(
    override_repeated_fields: list[RepeatableFields] | None = None, use_gunderson_repeat_names: bool = True
) -> FormVars:
    """

    Args:
        override_repeated_fields:
        use_gunderson_repeat_names: Our repeat variable values in the CE jsons are different than the actual variable
                                    names that are repeated, so you need a mapping dict

    Returns:

    """
    logger.debug(f"mock_formvars started with override_repeated_fields: {override_repeated_fields}")
    if override_repeated_fields is None:
        logger.debug("unique_repeatable_fields is None... prepare random sample...")
        unique_repeatable_fields = random.sample(
            [el.value for el in RepeatableFields],
            k=random.randint(0, len(RepeatableFields)),
        )
    else:
        logger.debug("unique_repeatable_fields is NOT None...")

        unique_repeatable_fields = [el.value for el in override_repeated_fields]
        if use_gunderson_repeat_names:
            var_name_to_template_val_lookup = {v: k for k, v in GD_HUMAN_REPEAT_SELECTIONS_TO_VAR_NAMES.items()}
            unique_repeatable_fields = [var_name_to_template_val_lookup[v] for v in unique_repeatable_fields]

    logger.debug(f"unique_repeatable_fields: {unique_repeatable_fields} {[type(v) for v in unique_repeatable_fields]}")

    return FormVars(
        StockholderInfoSame=unique_repeatable_fields,
        BroadDescriptionAssignedTechnology_S1="Some Technology",
        UsingTopTemplateFlag=True,
        UsingTopTemplateFlagFO_IAL="Yes",
        UsingTopTemplateFlag_IA="Yes",
        Waiver220=True,
        IndemnificationAgrIncluded=True,
        EmployeeNoncompete=True,
    )


def mock_bylawvars() -> BylawVars:
    return BylawVars(
        RoFR=True,
        QuasiCA=True,
        TransferRestrictions=True,
        TransferRestrictionsLanguage=True,
        TransferRestrictionDate=True,
        TransferRestrictionStock=TransferRestrictionEnum.ALL_STOCK,
        TransferDate="2023-12-31",
        DirectListingTransfer=True,
    )


def generate_mock_objs(
    company: Company | None = None,
    stockholders: list[Stockholder] | None = None,
    directors: list[Director] | None = None,
    stockholder_count: int = 3,
    include_founder_pref: bool | None = None,
    override_repeated_fields: list[RepeatableFields] | None = None,
) -> tuple[list[Stockholder], Company, list[Director], FormVars, BylawVars]:
    # Generate a mock company
    if company is None:
        company = mock_company()

    # Make sure to update FFPreferred flag as appropriate
    if include_founder_pref is not None:
        company.FFPreferred = include_founder_pref
    else:
        company.FFPreferredSharesAuthorized = None
        company.FFPreferredPricePerShare = None

    # Generate mock FormVars and BylawVars
    form_vars = mock_formvars(override_repeated_fields=override_repeated_fields)
    bylaw_vars = mock_bylawvars()

    if stockholders is None:
        logger.debug("generate_mock_objs() - stockholders was None... generate stockholders")
        stockholders = [mock_stockholder() for _ in range(0, stockholder_count)]
    else:
        logger.debug(f"generate_mock_objs() - stockholder objs provided: {stockholders}")

    initial_stockholder_name_set = {sh.Stockholder for sh in stockholders}

    founder_pref_count, common_stock_count = sum_shares(stockholders)

    if founder_pref_count > 0:
        logger.debug("WARNING - stockholders generated or provided have FFPREFERRED... MUST update company accordingly")
        company.FFPreferred = True

    # Now we need to calculate proper total authorized shares
    total_authorized = founder_pref_count + common_stock_count + company.SharesReservedStockPlan
    company.SharesAuthorized = total_authorized

    # Generate mock directors based on the company's NumberDirectors property
    if directors is not None:
        logger.debug(
            "WARNING - You've manually specified mock directors BUT there is a mismatch in director count between "
            "company NumberDirectors var and director list length - OVERRIDE company value"
        )
        company.NumberDirectors = len(directors)
        mock_directors = directors
    else:
        mock_directors = [mock_director() for _ in range(company.NumberDirectors)]

    final_stockholder_name_set = {sh.Stockholder for sh in stockholders}

    logger.debug(
        f"generate_mock_objs - initial name set {initial_stockholder_name_set} vs final {final_stockholder_name_set}"
    )

    return stockholders, company, mock_directors, form_vars, bylaw_vars


def generate_mock_xml_elements(
    stockholders: list[Stockholder],
    company: Company,
    directors: list[Director],
    form_vars: FormVars,
    bylaw_vars: BylawVars,
) -> list[ET.Element]:
    return [
        *convert_pydantic_to_xml_elem(form_vars),
        *convert_pydantic_to_xml_elem(bylaw_vars),
        *convert_pydantic_to_xml_elem(company),
        *list(
            itertools.chain.from_iterable(
                [
                    convert_pydantic_to_xml_elem(
                        stockholder,
                        counter=index,
                        repeat_fields=form_vars.StockholderInfoSame,
                    )
                    for index, stockholder in enumerate(stockholders)
                ]
            )
        ),
        *list(
            itertools.chain.from_iterable(
                [
                    convert_pydantic_to_xml_elem(director, override_repeat_context=f"[{index+1}]")
                    for index, director in enumerate(directors)
                ]
            )
        ),
    ]


def generate_mock_ce_xml_tree(
    company: Company | None = None,
    stockholders: list[Stockholder] | None = None,
    directors: list[Director] | None = None,
    stockholder_count: int = 3,
    include_founder_pref: bool | None = None,
    override_repeated_fields: list[RepeatableFields] | None = None,
) -> ET.ElementTree:
    """
    Given Pydantic model instances for company, stockholders, directors, etc., generate a mock questionnaire.

    Args:
        company:
        stockholders:
        directors:
        stockholder_count:
        include_founder_pref:
        override_repeated_fields:

    Returns:

    """

    (mock_stockholders, mock_company, mock_directors, mock_form_vars, mock_bylaw_vars,) = generate_mock_objs(
        company=company,
        stockholders=stockholders,
        stockholder_count=stockholder_count,
        directors=directors,
        include_founder_pref=include_founder_pref,
        override_repeated_fields=override_repeated_fields,
    )

    return xml_elements_to_ce_xml_tree(
        generate_mock_xml_elements(
            stockholders=mock_stockholders,
            company=mock_company,
            directors=mock_directors,
            form_vars=mock_form_vars,
            bylaw_vars=mock_bylaw_vars,
        )
    )


def generate_mock_ce_json_str(
    company: Company | None = None,
    stockholders: list[Stockholder] | None = None,
    directors: list[Director] | None = None,
    stockholder_count: int = 3,
    include_founder_pref: bool | None = None,
    override_repeated_fields: list[RepeatableFields] | None = None,
) -> str:
    """
    Given some Pydantic model instances that describe an incorporation, generate the JSON string that the equivalent
    questionnaire would produce when exported from CE via the API. We need this for tests.

    Args:
        company: Company instance
        stockholders: List of stockholder instances. If none are provided, stockhoder_count will be generated.
        directors: List of director instances
        stockholder_count: Total number of stockholders to be generated where none are provided
        include_founder_pref: Issue founder preferred
        override_repeated_fields: The repeat fields - e.g. re-use shares issued or re-use vesting commencement date for
        all stakeholders - will be selected randomly, BUT you can override the randomly generated values with this input

    Returns: Serialized JSON that CE platform would export for these objects (based on Gunderson template)

    """

    logger.debug(f"generate_mock_ce_json_str() - generate with following repeat fields: {override_repeated_fields}")
    xml_tree = generate_mock_ce_xml_tree(
        company=company,
        stockholders=stockholders,
        stockholder_count=stockholder_count,
        directors=directors,
        include_founder_pref=include_founder_pref,
        override_repeated_fields=override_repeated_fields,
    )

    ce_json_tree = convert_ce_answers_xml_to_json_string(xml_data=xml_tree)

    return ce_json_tree
