"""
This is flaminglog
"""

__all__ = [
        'make_json',
        'filter_json',
        'parse_filter_dict',
        'run_multiple_filters',
        'make_svg',
        'svg_to_png',
        'cleanup',
        'remove_png_files',
        'handle_error',
        'save_json',
        'load_json'
]

from .logrule import *
