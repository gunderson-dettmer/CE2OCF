# QuickStart

We've provided a couple examples of how to get started using ce<sub>2</sub>OCF using a high-level, medium-level and
low-level API.

# High-level API - Use Prebuilt Pipeline.

Assuming you want to produce OCF files and have minimal changes you want to make to our [datamaps parsing
configuration files](../Ce2Ocf/datamap/defaults), we recommend looking at
[`Ce2Ocf.ocf.pipeline.py`](../Ce2Ocf/ocf/pipeline.py), specifically the
`translate_ce_inc_questionnaire_datasheet_items_to_ocf(...)` function.

If you happen to use our exact CE variable conventions (unlikely, but bear with me), then, good news, there is just a
single required argument - a list of CE JSONs for your target questionnaire (**NOTE** we're assuming throughout this
quick start you have valid, complete questionnaire data).

In this scenario, first call `translate_ce_inc_questionnaire_datasheet_items_to_ocf(...)` to generate ocf file contents:

```python
import json
from pathlib import Path
from Ce2Ocf.types.dictionaries import ContractExpressVarObj
from Ce2Ocf.ocf.pipeline import translate_ce_inc_questionnaire_datasheet_items_to_ocf
from Ce2Ocf.ocf.postprocessors import (
    gunderson_repeat_var_processor,
    convert_state_free_text_to_province_code,
    convert_phone_number_to_international_standard
)
from Ce2Ocf.datamap.definitions import RepeatableDataMap
from Ce2Ocf.ocf.datamaps import (
    AddressDataMap,
    PhoneDataMap,
    RepeatableVestingStockIssuanceDataMap
)
from Ce2Ocf.ocf.generators.vesting_enums_to_ocf import generate_ocf_vesting_schedule_from_vesting_drivers

# You need to get these from somewhere... here we're loading a sample from the repo root
with Path("tests/fixtures/ce_datasheet_five_stockholders.json").open("r") as ce_data:
    ce_jsons: list[ContractExpressVarObj] = json.loads(ce_data.read())

RepeatableDataMap.register_handlers({"repeated_variables": gunderson_repeat_var_processor})
RepeatableVestingStockIssuanceDataMap.register_handlers(
    {"repeated_variables": gunderson_repeat_var_processor}
)
AddressDataMap.register_handlers(
    {"country_subdivision": lambda x, _: convert_state_free_text_to_province_code(x)}
)
PhoneDataMap.register_handlers(
    {"phone_number": lambda x, _: convert_phone_number_to_international_standard(x)}
)

translated_data = translate_ce_inc_questionnaire_datasheet_items_to_ocf(
    ce_jsons,
    pref_stock_issuance_custom_post_processors={
        "repeated_variables": gunderson_repeat_var_processor
    },
    common_stock_class_custom_post_processors={
        "repeated_variables": gunderson_repeat_var_processor
    },
    vesting_schedule_custom_post_processors={
        "vesting_schedule": generate_ocf_vesting_schedule_from_vesting_drivers
    }
)
```

You'll notice we have a bunch of post-processor registered. Let's go through these one at a time, from the most generally
applicable to the least:
1. `convert_state_free_text_to_province_code()` - this is a general-purpose post-processor that is designed to match
   a wide variety of correct (and incorrect) country and province codes and produce a consistent format. We use this to
   ensure that the questionnaire values for US states are converted to acceptable OCF values. You will probably want
   to use this. Note that we only need to register it at the class level once and then all datamaps that have this
   class nested will automatically call the post processor on their nested `address.country_subdivision` field
2. `convert_phone_number_to_international_standard()` - like #1, this is a general-purpose post-processor to try to
   conform phone numbers to international (and OCF) standards. Like #1, note we only need to register it on the
   `PhoneDataMap` class once and then all nested `PhoneDataMap` datamaps will apply the same post processor to their
   `phone_number` fields.
3. `generate_ocf_vesting_schedule_from_vesting_drivers` - this may be less applicable, but most likely you can use this
   too. Like most questionnaires, we suspect, ours lets users specify vesting by allowing the selection of a couple
   enumerate values. For our supported values look in [`Ce2Ocf.types.enums`](../Ce2Ocf/types/enums.py). Our three
   supported vesting schedules are in `VestingTypesEnum` (custom is not supported for OCF but is an option). We also
   support the single and double trigger acceleration values in `SingleTriggerTypesEnum` and `DoubleTriggerTypesEnum`,
   respectively. In `VestingScheduleInputsDataMap`, we define all the enums that drive our vesting schedule as child
   properties of a single field `vesting_schedule`. passing `{"vesting_schedule":
   generate_ocf_vesting_schedule_from_vesting_drivers}` as the `vesting_schedule_custom_post_processors` argument to
   `translate_ce_inc_questionnaire_datasheet_items_to_ocf()` will register this post-processor on the `vesting_schedule`
   field of `VestingScheduleInputsDataMap`. All of those enum values are then available to the post processor, which
   uses the utility fuctions in `Ce2Ocf.ocf.generators` to create valid OCF vesting schedules based on the selected
   enums. If you use the same enums (or can switch to them), you can use our post-processor.
4. `gunderson_repeat_var_processor()` - this is probably not applicable to your template, but we needed to include
   it for our purposes. In our template, when a user selects which stockholder fields to repeat accross all stockholders
   such as Vesting, SingleTrigger, VCD, etc., the values produced by the multi-select are human-friendly strings that
   must be mapped to the actual CE variable names we'd want to look up for all repetitions. E.g. if we want all
   stockholders to have the same vesting schedule, our `StockholderInfoSame` value would be ["Vesting Schedule"] but the
   variable containing vesting schedule types for each stockholder is called `Vesting` in our template. For our CE
   parser to retrieve the proper repeated value for every stockholder, we need to lookup `Vesting` and we use the
   `gunderson_repeat_var_processor()` post-processor to do this mapping.

We can then package the resulting ocf objets into ocf files and, finally, a zip archive:

```python
# Call package_translated_ce_as_valid_ocf_files_contents() with translated_data
ocf_files_contents = package_translated_ce_as_valid_ocf_files_contents(translated_data)

# Call package_ocf_files_contents_into_zip_archive() with ocf_files_contents
zip_archive_bytes = package_ocf_files_contents_into_zip_archive(ocf_files_contents)

with open("test.ocf.zip", "wb") as f:
    f.write(zip_archive_bytes)
```

If you look at the args available on `translate_ce_inc_questionnaire_datasheet_items_to_ocf()`, you'll see you can
provide custom datamaps for all key ocf object types, as well as custom post-processors. You can also provide custom
static `value_overrides` which will be searched before CE variables. So, for, example, if I wanted to override all
vesting to 4yr with 1yr Cliff, we could call translate_ce_inc_questionnaire_datasheet_items_to_ocf with a
`vesting_schedule_custom_value_overrides` argument of `{"Vesting":"4yr with 1yr Cliff"}`. If we want to specify custom
datamaps or post processors, look for the applicable named argument on the function. They have type hints for your
convenience.

# Medium-level API Documentation

The medium-level API acts as an intermediary between the high-level API in `pipeline.py` and the low-level API in
`Ce2Ocf.datamap.loaders` and `Ce2Ocf.datamap.crawler`. It provides a set of functions to parse different types of
Contract Express data into Open Cap Table Format (OCF) compliant data. **Note** the high-level API we presented above
using `translate_ce_inc_questionnaire_datasheet_items_to_ocf()` is just a wrapper to orchestrate calling the
medium-level API functions below to produce all required OCF object types.

Here are the main functions provided by the medium-level API:

- `parse_ocf_issuer_from_ce_jsons()`: This function parses an OCF issuer object from a list of CE JSON objects using
  either a default or a custom datamap.

- `parse_stock_plan_from_ce_jsons()`: This function parses an OCF stock plan object from a list of CE JSON objects
  using either a default or a custom datamap.

- `parse_ocf_stock_class_from_ce_jsons()`: This function parses an OCF stock class object from a list of CE JSON
  objects. It can parse either common or preferred stock classes based on the `common_or_preferred` argument.

- `parse_ocf_stock_legend_from_ce_jsons()`: This function parses an OCF stock legend object from a list of CE JSON
  objects. It can parse either common or preferred stock legends based on the `common_or_preferred` argument.

- `parse_ocf_stakeholders_from_ce_json()`: This function parses a list of OCF stakeholder objects from a list of CE JSON
  objects using either a default or a custom datamap.

- `parse_ocf_stock_issuances_from_ce_json()`: This function parses a list of OCF stock issuances from a list of CE JSON
  objects. It can parse either common or preferred stock issuances based on the provided datamaps and value overrides.

- `parse_ocf_vesting_schedules_from_ce_json()`: This function parses a list of OCF vesting schedules from a list of CE
  JSON objects using either a default or a custom datamap.

- `parse_ocf_vesting_events_from_ce_json()`: This function generates vesting start events for each stockholder based on
  their vesting schedule.

All the functions support the use of post processors to further process the parsed data.

# Low-level API Documentation

The low-level API provides the foundational functionality that the medium and high-level APIs build upon. It consists
of (1) [datamap objects](datamaps.md) defining the target datashape, (2)
[datamap variable lookup configurations](configuring%20datamap%20lookups.md) which describe how to look up values
from CE to populate the target datashape, and (3) a
[function called `traverse_datamap()`](configuring%20datamap%20lookups.md) which uses the datamap, plus the lookup
configuration plus CE JSONs to produce a desired object.

## Variable Lookup Configurations + Loaders

The loaders are responsible for loading datamaps. A datamap is a JSON file that maps CE data fields to OCF data fields.
Loaders are used to load default datamaps or custom datamaps if they are provided. The main loader functions include:

- `load_ce_to_ocf_issuer_datamap()`
- `load_ce_to_ocf_stock_plan_datamap()`
- `load_ce_to_ocf_stock_class_datamap()`
- `load_ce_to_ocf_stock_legend_datamap()`
- `load_ce_to_ocf_stakeholder_datamap()`
- `load_ce_to_ocf_vesting_issuances_datamap()`
- `load_ce_to_ocf_vested_issuances_datamap()`
- `load_vesting_events_driving_enums_datamap()`
- `load_vesting_schedule_driving_enums_datamap()`

## Crawler

The crawler module contains the `traverse_datamap()` function, which is responsible for traversing the datamap and
converting CE data fields into OCF data fields. It takes in a datamap, a list of CE JSONs, and optional parameters
like value overrides and a flag to specify whether to fail on missing variables. It returns a dictionary or a list of
dictionaries representing OCF compliant data.

The `traverse_datamap()` function supports nested datamaps, allowing for complex mappings between CE and OCF data
fields. It also supports the use of post processors to further manipulate the mapped data.

## Non-0CF Data

If you wanted to define your own object types, you could use the primitive datamap building blocks in
[Ce2Ocf.datamap.definition](../Ce2Ocf/datamap/definitions.py) to construct a datamap with your desired schema. Follow
our guidance in [the datamap documentation](datamaps.md) for more how this can be done or look at the ocf datamaps
for [examples of real Python datamaps look like](../Ce2Ocf/ocf/datamaps.py) and then the corresponding [parser
variable lookup jsons](../Ce2Ocf/datamap/defaults) to see how to define a variable lookup for your datamap. Once you have
the python datamap plus the variable lookup json, you can use these, plus `traverse_datamap()` plus CE JSONs
from a complete questionnaire to produce your target object.
