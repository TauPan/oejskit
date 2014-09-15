import py

def pytest_namespace():
    return {
        'jstests_browser_specs' :
            {'supported': ['firefox', 'iexplore', 'safari']}
        }

