# CE JSON Outputs

The process of converting Contract Express (CE) template variables to their corresponding JSON format is an essential
aspect of understanding how data is structured and retrieved from CE templates. Let's delve into the conversion
process and then exemplify this with some common CE syntaxes.

### Understanding the Conversion Process

1. **Variable Declaration in Templates**: In CE, variables are declared within templates to capture specific data points. The naming convention and structure of these variables play a crucial role in how they are interpreted and later transformed into JSON.

2. **Conversion to JSON Format**: When these variables are processed, they are translated into a JSON format, where each variable is represented as an object with properties like `name`, `values`, and `repetition`.

3. **Handling Repeated and Nested Variables**: Repeated and nested variables are particularly important. They are handled by assigning them unique identifiers and structuring the JSON to reflect their repeated nature.

### Examples of CE Syntax to JSON Output

#### Simple Variable
- **CE Syntax**: `{BuyerName}`
- **JSON Output**:
  ```json
  {
    "name": "BuyerName",
    "values": ["Acme Corp"],
    "repetition": null
  }
  ```

#### Repeated Variable
- **CE Syntax**: `[Repeat NumberOfItems{ItemDescription}]`
- **JSON Output**:
  ```json
  [
    {
      "name": "ItemDescription",
      "values": ["Item 1 Description"],
      "repetition": "[1]"
    },
    {
      "name": "ItemDescription",
      "values": ["Item 2 Description"],
      "repetition": "[2]"
    }
  ]
  ```

#### Nested Repeated Variable
- **CE Syntax**:
  ```
  [Repeat Projects{ProjectName
    [Repeat ProjectMilestones{MilestoneDescription}]
  }]
  ```
- **JSON Output**:
  ```json
  [
    {
      "name": "ProjectName",
      "values": ["Project Alpha"],
      "repetition": "[1]"
    },
    {
      "name": "MilestoneDescription",
      "values": ["Milestone 1 for Project Alpha"],
      "repetition": "[1]"
    },
    {
      "name": "MilestoneDescription",
      "values": ["Milestone 2 for Project Alpha"],
      "repetition": "[2]"
    }
  ]
  ```

#### Special Case to Re-Use Repeat 1 Value in Subsequent Repeats
- **CE Syntax**: `{Vesting_S1}`
- **JSON Output**:
  ```json
  {
    "name": "Vesting_S1",
    "values": ["100% after 2 years"],
    "repetition": null
  }
  ```

### Conclusion

The transformation from CE template variables to JSON format is critical for understanding how data is managed and retrieved in CE systems. The structure of the JSON output reflects the complexity and hierarchy of the data within the template, accommodating simple, repeated, and nested variables. Understanding this conversion process is essential for effectively utilizing and processing data from CE templates.
