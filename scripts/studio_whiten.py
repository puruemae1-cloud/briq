#!/usr/bin/env python3
"""Compatibility shim — studio mats now map to Gucci DarkGray, not pure white.

All scrapers / weekly syncs historically imported `studio_whiten`. Keep those
imports working while routing to `studio_greymat`.
"""
from studio_greymat import (  # noqa: F401
    DEFAULT_DIRS,
    TARGET_RGB,
    collect_images,
    greymat_dirs,
    greymat_file,
    save_product_image,
    studio_bg_color,
    whiten_array,
    whiten_dirs,
    whiten_file,
)

__all__ = [
    "DEFAULT_DIRS",
    "TARGET_RGB",
    "collect_images",
    "greymat_dirs",
    "greymat_file",
    "save_product_image",
    "studio_bg_color",
    "whiten_array",
    "whiten_dirs",
    "whiten_file",
]
