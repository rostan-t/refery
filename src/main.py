from src.test_suite import get_testsuites


def main() -> int:
    testsuites = get_testsuites()

    exit_code = 1
    for testsuite in testsuites:
        exit_code &= bool(testsuite.run())

    return exit_code


if __name__ == '__main__':
    exit(main())
