"""
CSS_METHOD = inline
Since global-styles endpoint is not available, CSS is embedded
directly in each page's HTML content as a <style> block.
This module provides the get_css() helper used by all page scripts.
"""
import os

CSS_PATH = "/root/ieee-gju/assets/style.css"


def get_css():
    """Return the full design system CSS as a <style> block."""
    with open(CSS_PATH) as f:
        css = f.read()
    return f"<style>\n{css}\n</style>"


if __name__ == "__main__":
    css_block = get_css()
    print(f"CSS block ready: {len(css_block)} chars")
    print("Usage: from tasks.inject_css import get_css")
