import pytest


def pytest_addoption(parser):
    parser.addoption('--db',
    dest='testdb',
    choices=["local", "faitout"],
    default='local',
    help='Specify db: "local", "faitout".')


@pytest.fixture(scope='session')
def testdb(request):
    return request.config.option.testdb
