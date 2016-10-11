import pytest
import sys
import configs


def main():
    plgns = [configs]
    options = " ".join(sys.argv[1:]) + ' --cov=fas tests/ --cov-report html:cov_html'
    pytest.main(options, plugins=plgns)

if __name__ == "__main__":
    main()
