# Overview

# Key Functions

## extract_ce_variable_val()

`extract_ce_variable_val()` is the key function we use look for variables in CE. It's built to account for our template
convention (discussed elsewhere, particularly in [Repeats](Repeats.md)), where we first want to see if a given value
is being repeated from a static copy of the first instance value of a repeated value with a specific suffix -
arg `first_instance_name_suffix`.

To help illustrate how the search logic works and why the breakdown is as it is, first, consider the CE JSON outputs
generated for **a)** a Gunderson template where we are re-using the Vesting variable value from the first shareholder vs
**b)** a template where you have to provide an answer for every stakeholder:

<table>
  <tr>
    <th>GD Var Value from SH 1 Reused</th>
    <th>Three Repeats, Values Chosen for Each Repeat</th>
  </tr>
  <tr>
    <td>
      <code>
        {
          "name": "Vesting_S1",
          "values": ["100%; all times after CiC"],
          "repetition": null
        }
      </code>
    </td>
    <td>
      <code>
        [
          {
            "name": "Vesting",
            "values": ["100%; all times after CiC"],
            "repetition": "[1]"
          },
          {
            "name": "Vesting_S1",
            "values": ["Fully Vested"],
            "repetition": "[2]"
          },
          {
            "name": "Vesting_S1",
            "values": ["100%; all times after CiC"],
            "repetition": "[3]"
          }
        ]
      </code>
    </td>
  </tr>
</table>

Our search logic in `extract_ce_variable_val` is as follows:

1. **When the Repetition Number is `None`**:
   - The function first searches for the variable with the `first_instance_name_suffix` appended
     (e.g., `ce_var_name_S1`) and a `None` repetition number. This will find first repeats that are being held static
     on subsequent loops.
   - If no match is found, it searches for the variable name as is (`ce_var_name`) with the repetition number also
     as `None`. This finds variables that are truly standalone (no repeat convention in the CE JSON)

2. **When the Repetition Number is an Integer**:
   - If the repetition number is `1`, the search order is the same as when the repetition number is `None` with slightly
     different backup:
     - First, it searches for the variable name with the `first_instance_name_suffix` and a `None` repetition number -
       e.g. ce_var_name_S1. Again, this picks up convention where a variable value is being repeated from the
       first repeat with a special static value.
     - If no result is found, it searches for the variable name without the suffix, but with the repetition number `1`.
       This will capture "traditional" CE repeats where there's no fancy repeating of first repeat value.
   - If the repetition number is greater than `1`:
     - The function first searches for the variable name without the suffix and with the given repetition number.
     - If no match is found, it then searches for the variable name with the `first_instance_name_suffix` and
       a `None` repetition number. This covers our repeat pattern where might repeat, for example, Vesting for three
       SHs from SH #1 and, thus, we don't collect anything for repeats 2 - 3.

In each case, if a matching variable object is found, the function returns the value obtained from the
`get_ce_obj_value_NEW` function applied to the first object in the list of matching variable objects. If no
matching variables are found, and `fail_on_missing_variable` is `True`, a `VariableNotFound` exception is raised.
Otherwise, the function returns `None`.

This approach ensures that the function searches for the variable in the order dictated by the context of its use,
respecting the nuances of how the Contract Express system manages variable names and repetition numbers in different
scenarios.
