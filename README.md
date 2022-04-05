# Refery

Refery is a functional test tool written in Python.

## Install

```
$ ./setup.py install
```

## Usage

```
usage: refery [-h] -f <path> [--verbosity <verbose|silent|normal>] [--junit-file <path>]

options:
  -h, --help            show this help message and exit
  -f <path>, --test-file <path>
                        Path to the YAML test file.
  --verbosity <verbose|silent|normal>
                        Output's verbosity, defaults to 'normal'.
  --junit-file <path>   Optional path to a JUnit XML file in which to write the output
```

As you can see, `refery`'s only mandatory argument is a path to the YAML file
describing the collection of test suites to be run.

## Writing tests

Individual tests are represented by test cases and a test suite is a collection
of test cases.

### Test suites

Test suites are a given as a
[YAML sequence](https://yaml.org/spec/1.0/#syntax-collect-seq) which is the
value associated to the
[YAML mapping](https://yaml.org/spec/1.0/#syntax-collect-map) key `testsuites`.

Each test suite is a YAML mapping which accepts the following fields:

| Field      | Description                                                                                 | Optional |
|------------|---------------------------------------------------------------------------------------------|:--------:|
| `name`     | Name of the test suite.                                                                     |    ❌     |
| `tests`    | YAML sequence containing the test cases.                                                    |    ✅     |
| `setup`    | Command to execute before each test case.                                                   |    ✅     |  
| `teardown` | Command to execute after each test case.                                                    |    ✅     |  
| `fatal`    | Indicates if a failure in a test case means an abortion of the runner. Defaults to `false`. |    ✅     |  

### Test cases

Each test case is a YAML mapping accepting the following fields:

| Name                        | Description                                                                                                                                                                                                                                                                                                                      | Optional |
|-----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------:|
| `name`                      | Name of the test case.                                                                                                                                                                                                                                                                                                           |    ❌     |
| `binary`                    | Path to the tested executable.                                                                                                                                                                                                                                                                                                   |    ❌     |
| `args`                      | YAML sequence containing the arguments passed to the executable.                                                                                                                                                                                                                                                                 |    ✅     |
| `ref`                       | Path to an executable with the desired behaviour.                                                                                                                                                                                                                                                                                |    ✅     |
| `stdin`                     | String passed as standard input.                                                                                                                                                                                                                                                                                                 |    ✅     |
| `stdout`                    | Expected standard output.                                                                                                                                                                                                                                                                                                        |    ✅     |
| `stderr`                    | Expected standard error.                                                                                                                                                                                                                                                                                                         |    ✅     |
| `exit_code`                 | Expected exit code.                                                                                                                                                                                                                                                                                                              |    ✅     |
| `skipped`                   | Boolean indicating whether the test case shall be ignored.                                                                                                                                                                                                                                                                       |    ✅     |
| `timeout`                   | Timeout in seconds, after which the test case is stopped marked as failed.                                                                                                                                                                                                                                                       |    ✅     |
| `stdout_mode`/`stderr_mode` | The testing mode of the two output streams. <br/>Can be of two kinds:<ul><li>`strict`: The actual value shall be the same as the expected value.</li><li>`exists`: If the expected value is not empty, the actual value shall not be empty and reciprocally.</li></ul> Both `stdout_mode` and `stderr_mode` default to `strict`. |    ✅     |

If the `ref` is specified, it is used to test the standard output, standard
error and exit code. If any of these fields is specified, they take precedence
over `ref`.

For example, take the following test case:

```yaml
hello:
  ref: bin/hello.sh
  exit_code: 0
```

The `stdout` and `stderr` are tested according to `bin/hello.sh` but the exit
code must be equal to `0`, no matter what is actually returned by
`bin/hello.sh`.

### Default value

An optional YAML mapping can be used to specify default values for all test
cases. It must be passed as a value to the `default` key and can contain all
fields accepted by test cases. For each test case, if a field is already
defined, the one defined in the test case takes precedence.

Here is an example of a valid input file :

```yaml
default:
  binary: my_hello.sh
  ref: bin/hello
  stderr_mode: exists

testsuites:
  - name: hello
    fatal: true
    tests:
      - name: simple_hello
      - name: hello_with_name
        timeout: 1
        args:
          - John Doe
  - name: goodbye
    tests:
      - name: bye
        ref: bin/goodbye
        timeout: 1
        args:
          - --bye
          - John Doe
```

This defines two test suites, the first containing two test cases and the second
only one. 
