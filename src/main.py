from src.test_suite import get_testsuite


def main() -> int:
    testsuite = get_testsuite()
    return testsuite.run()


if __name__ == '__main__':
    exit(main())
