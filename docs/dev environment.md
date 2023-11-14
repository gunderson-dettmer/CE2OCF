# Ce<sub>2</sub>Ocf Project Dev Environment Setup

## Overview

`Ce2Ocf` is a library created by Gunderson Dettmer Legal Engineering designed to read and parse data maps from Contract Express JSON exports into valid OCF (Open Cap Format). This project adheres to modern Python standards, requiring Python 3.9 or higher. It includes a robust testing suite, code style enforcement, and continuous integration tools to ensure code quality and reliability.

Below, you'll find detailed information about the various environments set up in this project, their purposes, setup instructions, and the commands available in each.

## Environments and Usage

### Default Environment

#### Purpose:
The default environment is configured for running tests and coverage reports. It is the primary environment for developers to validate their changes and ensure code quality.

#### Core Library & Test Dependency Setup:
Ensure you have Python 3.9 or higher installed, and then install the required dependencies.

```shell
pip install .[test]
```

#### Commands:
- `test`: Run the test suite using pytest.
  ```shell
  hatch run test
  ```
- `test-cov`: Execute the test suite with coverage.
  ```shell
  hatch run test-cov
  ```
- `cov-report`: Generate a coverage report.
  ```shell
  hatch run cov-report
  ```
- `cov`: Run the full coverage test (both `test-cov` and `cov-report`).
  ```shell
  hatch run cov
  ```
- `install-pre-commit`: Install the pre-commit hooks.
  ```shell
  hatch run install-pre-commit
  ```

### Lint Environment

#### Purpose:
The lint environment is for static code analysis. It includes tools like `black`, `mypy`, `ruff`, etc., to enforce a consistent code style and perform static type checking.

#### Setup:
To set up the lint environment, you will need to install the linting dependencies separately.

```shell
pip install .[lint]
```

#### Commands:
- `typing`: Run type checks with `mypy`.
  ```shell
  hatch run lint:typing
  ```
- `style`: Check code formatting with `ruff` and `black`.
  ```shell
  hatch run lint:style
  ```
- `fmt`: Automatically format the code.
  ```shell
  hatch run lint:fmt
  ```
- `all`: Run all linting steps (style and typing checks).
  ```shell
  hatch run lint:all
  ```

## Additional Configuration

### Black and Ruff

Configurations for `black` and `ruff` are specified for consistent code styling. These tools will enforce a line length of 120 characters and target Python 3.7 for compatibility.

### Coverage

The `coverage` configuration is set to include the `Ce2Ocf` library and its tests, with certain lines and files excluded from the report to not penalize the coverage score unnecessarily.


## Contribution and Development

Contributors should clone the repository and set up the above environments locally. It's encouraged to write tests alongside new features and to use the linting tools to maintain code quality. Remember to check your code against all Python versions specified in the test matrix before submitting a pull request.
