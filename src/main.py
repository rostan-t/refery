import junit_xml

from src.test_suite import get_testsuites


def main() -> int:
    testsuites, junit_file = get_testsuites()

    exit_code = 1
    for testsuite in testsuites:
        exit_code &= bool(testsuite.run())

    if junit_file is not None:
        junit_testsuites = (t.junit_test_suite for t in testsuites)
        with open(junit_file, 'w') as file:
            file.write(junit_xml.to_xml_report_string(junit_testsuites))

    return exit_code


if __name__ == '__main__':
    exit(main())
