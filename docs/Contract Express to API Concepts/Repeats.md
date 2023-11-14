# Repeats in Contract Express API Outputs

To understand how repeated variables in Contract Express templates translate into API outputs, we need to first grasp the concept of repeats in the templates and then see how they are represented in the JSON outputs.

### Repeated Variables in Contract Express Templates

1. **Purpose of Repeats:** Repeated variables are used when you need to collect information on multiple instances of a similar entity (e.g., names of multiple guarantors, supplier names, project milestones, etc.). The number of these entities can vary per transaction.

2. **Implementation:** A repeat span is added to the document, marked with the `Repeat` keyword. For example: `[Repeat NumberOfMilestones{MilestoneDescription} due on {MilestoneDate}]`. Here, `MilestoneDescription` and `MilestoneDate` become repeated variables.

3. **Referring to Repeated Variables:** Outside the repeat span, these variables are referred to using the `Collect` function, e.g., `Collect(MilestoneDescription)`.

4. **Induced and Explicit Repeats:** The number of repetitions can be set explicitly (e.g., asking "How many milestones?") or induced implicitly (allowing users to add more entries via UI controls). This is controlled by the "Calculated from Repeat" checkbox.

5. **RepeatCounter and RepeatContext:** These are special variables used within repeat spans. `RepeatCounter` refers to the instance number of the repeated item, while `RepeatContext` gives the full context of that item.

### Translating to JSON Outputs

When these repeats are extracted via the API, their representation changes to a JSON format. Let's analyze some examples:

1. **Simple Repeats:**
   ```json
   {
     "name": "Stockholder",
     "values": ["Janice L"],
     "repetition": "[2]"
   }
   ```
   Here, "Stockholder" is a repeated variable. The "repetition" field shows the instance number `[2]`, meaning this is the second instance of the "Stockholder" variable.</br></br>

2. **Non-Repeated Variables:**
   ```json
   {
     "name": "SoleIncorporator",
     "values": ["John \"The Coder"],
     "repetition": null
   }
   ```
   Non-repeated variables have their "repetition" field as `null`.</br></br>

3. **`_S1` Convention to Repeat First Repeat**</br></br>

   As described below in [Repeating Values from First Repeat](#repeating-values-from-first-repeat) We use the
_S1 suffix to indicate that a repeated variable should carry the value of the first instance of the repeated
variable across all its instances. This is particularly useful when certain attributes, like Vesting or
SingleTrigger in your example, need to be consistent across all repetitions of an entity (e.g., stockholders). </br></br>

   **JSON Examples from CE API**</br></br>

   - **Standard Repeated Variables (without `_S1`):**
     This example demonstrates a typical repeated variable, representing the second instance of the "Stockholder" entity.
     ```json
     {
       "name": "Stockholder",
       "values": ["Janice L"],
       "repetition": "[2]"
     }
     ```
   - **Variables with the `_S1` Suffix:**
     This indicates that the `Vesting` variable for all instances of a repeat (e.g., all stockholders) should use the value "100%; all times after CiC". The `repetition` field being `null` signifies it's not an individually repeated value but a shared value across all instances.
     ```json
     {
       "name": "Vesting_S1",
       "values": ["100%; all times after CiC"],
       "repetition": null
     }
     ```
     This example shows that the `Vesting` variable is consistently set to "100%; all times after CiC" for every instance.

### Special Cases

#### Re-Using Values from First Variable Repeat Instance

At Gunderson, we use a special convention to allow you to re-use the first answer for a particular variable for
subsequent repeats. For example, let's say that you have 4 stockholders in a company, but you want all of them to have
the same value for `Vesting` and `SingleTrigger` variables. The simple way to do this is to have four repeats and fill
out each repeat with the same value.

It's much nicer for users to fill this out once. CE doesn't have an easy way to do this, but there is a convention that
works for this, which we use. We have a dropdown to select certain variable names to re-use the first repeat values and
then, when one or more of these are selected, we copy the value of the first repeat of the given variable to a special
variable with the same name plus a suffix `_S1`. Following our example above, we'd have `Vesting_S1` and
`SingleTrigger_S1` and where `Vesting` and `SingleTrigger` are selected to be the same across all repetitions of Vesting
and SingleTrigger. We typically do this in a special multi-select variable `StockholderInfoSame`. Then, when we parse
the ce variables, our CE variable extractor automatically looks for the values of `Vesting_S1` and `SingleTrigger_S1`
for *every* repetition.

Our CE variable parser `extract_ce_variable_val()` defaults to our convention, so you don't need to handle this
yourself, but you can tweak it to your purposes. For example, you can turn this search behavior off by setting
`first_instance_name_suffix` to `None`. Alternatively, if you provide a function that accepts a string and returns a
string to `first_instance_name_suffix`, the function will automatically search for a variable in that follows your
convention - e.g if you have a **prefix** `static_` plus a var name you'd set `first_instance_name_suffix` like this:

```commandline
first_instance_name_suffix: lambda var_name: f"static_{var_name}"
```

### Conclusion

In summary, the repeats in Contract Express templates are a way to handle multiple instances of similar data fields. In the API output, each instance is represented as a separate entity with a repetition index indicating its order or hierarchy. Understanding this mapping is crucial for correctly processing and utilizing the data from the API in your application.
