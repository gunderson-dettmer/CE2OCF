# CE<sub>2</sub>OCF Project Structure

## Overview

CE<sub>2</sub>OCF is a comprehensive library designed for converting Contract Express (CE) data to Open Cap Format
(OCF). It is structured modularly to handle different aspects of this complex process. The **ce** package deals with CE
data manipulation, including mock data generation, transformations between XML and JSON formats, and a parser for CE
JSONs. The **datamap** package is pivotal, transforming CE JSONs into OCF using Pydantic dataclasses that map CE
variables to OCF variables. This package includes default datamaps, data crawlers, loaders, and parsers with special
functionalities like string templates and math evaluation. The **ocf** package provides utilities for OCF data types,
including generators for OCF vesting types and conditions, mocks for COF objects, schema loading, a CE to OCF processing
pipeline, postprocessors for data transformation, and OCF validators. Additionally, there's a **types** package for
library-specific type definitions and a **utils** package offering auxiliary support functions and classes. This
structured approach enables efficient and flexible handling of complex data conversions between CE and OCF formats.

## Package and Module Overview

There's a lot to unpack in this library as converting to OCF is quite complicated. That said, we've tried to arrange
everything into distinct modules that separate code into specific concerns:

1. **ce**: This package contains code related to contract expressdata manipulation.
   - **mocks**: Is used in tests, but lets you generate mock questionnaire XML and JSON, so you may find these
     capabilities useful for other purposes. We've included these capabilities in the core library for these reasons.
   - **transforms**: Provides modules to convert to and from XML and JSON CE formats. CE's web gui will give you
     questionnaire data in XML whereas the API gives you JSON. Our documentation is primarily concerned with the JSON
     outputs of the API, but you could use some of the utilities in here to convert from xml to json. We may add more
     documentation on this in the future, but, for now, the library is targeted at JSON outputs.
   - **parser.py**: This module contains our functions to parse values out of the lists of CE JSONs you'll retrieve
     from the API.

2. **datamap**:  This package does the heavy-lifting of transforming CE JSONs into OCF. At its heart, we have a number
   pydantic dataclasses that describe a JSON format mapping ocf variable names to various CE template values. There are
   a number of special tricks available in these JSONs, including string templates, math evaluation and the ability to
   extract repeats of CE variables into distinct objects - one for each repeat. See more [here](datamaps.md)
   - **[defaults](../Ce2Ocf/datamap/defaults)**: These are the default datamap jsons that are loaded if you don't provide your own. They're mapped to
     Gunderson's defaults, but they'll likely be a great starting point if you want to create your own.
   - **crawler.py**: Contains the code that crawls our datamap definitions and then parses CE JSONs for specified
                     values.
   - **definitions.py**: These are the pydantic definitions of the building-block data schemas that tell the
     `traverse_datamap()` how to parse a given schema. See more [here](datamaps.md).
   - **loaders.py**: Helper functions to load datamap jsons into pydantic datamap objects.
   - **parsers.py**: These are helper functions to automatically 1) load a datamap, 2) register post processors for
                     certain fields - e.g. formatting functions for phone numbers and 3) parse CE Jsons to produce the
                     desired OCF JSON.

3. **ocf**: This package contains utilities for OCF data and datatypes.
   - **generators**: Contains a number of utility functions to generate the building blocks of OCF vesting types and
     objects.
     - **ocf_vesting_conditions.py**, **ocf_vesting_events.py**: This module contains a number of functions to create
       OCF vesting conditions based on certain inputs. Most likely, your questionnaire uses enumerations to specify
       vesting and vesting-related data. You need to convert that into a very specific OCF data structure. We use the
       functions in here to create the required vesting conditions.
     - **vesting_enums_to_ocf.py**: Similar to `ocf_vesting_conditions.py`, this is higher-level and is designed to take
       a few enums - e.g. vesting schedule type, single trigger accel type, double trigger accel type and VCD and use
       those to generate a valid OCF vesting schedule. This is very complex and we welcome additional eyes on how we're
       doing this here.
   - **mocks** (within ocf): Contains mock COF objects, again used for tests but included in the main package as this
     may be useful to you.
   - **schema**: We'd like to move this and load OCF dynamically, but, for the time being, we load ocf schemas (v 1.1.0)
     from here into our validator.
   - **pipeline.py**: Contains a pre-built CE to OCF processing pipeline with decent configurability. It loads our
     default datamaps, but you can easily provide your own. The resulting OCF JSONS are packaged into OCF files.
     :bulb: **Tip:** If you're building your own processor, you'll want to start here.
   - **postprocessors.py**: As you'll see elsewhere in the docs, many of our datamaps are built from a custom child
     class of a pydantic BaseModel called `FieldPostProcessorModel`. It lets you register class-wide "post-process"
     functions which, after the model is built from CE data, will provide the value for a given property to the
     registered post-processor and replace the original value for that key with whatever is produced by the
     post-processor.
   - **validator.py**: Tools to validate OCF against OCF schemas.
   - **datamaps.py**: Our OCF-specific datamaps built from the base datamaps in `datamap.definitions.py`

6. **types**:
   - Contains type definitions for the library with `dictionaries.py`, `enums.py`, `exceptions.py`, `models.py`,
     and `protocols.py`.

7. **utils**:
   - Contains utility functions or classes that support the library's operations.
