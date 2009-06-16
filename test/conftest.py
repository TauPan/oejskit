pytest_plugins = "jstests"

pytest_option_jstests_reuse_browser_windows = True

jstests_browser_specs = {
    'supported': ['firefox', 'iexplore'],
}
