"""Helper functions for testing pipelines"""

def mock_function(a, p):
    """Mock function for testing - concatenates parameters with underscore"""
    return f"{a}_{p}"

def transform_function(a, p):
    """Transform function for testing - concatenates parameters with underscore"""
    return f"{a}_{p}"