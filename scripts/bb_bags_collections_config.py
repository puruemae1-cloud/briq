"""Burberry Bags → Collections hub map.

Sourced from https://int.burberry.com/c/bags/ Collections nav:
Check / Cotswolds / Highlands / Horseshoe / Bloomsbury / B Clip / Margate.

Women/Men type bags (mini, tote, crossbody, …) already exist in women/men configs
and are intentionally not duplicated here.
"""

from __future__ import annotations

# (briq_id, label_en, plp_path, briq_top_category, parent_group)
# Check Bags spans women + men PLPs — same parent; scrape tags both under their ids,
# and subcategoryGroups merges them for the Check Bags chip.
BAGS_COLLECTIONS: list[tuple[str, str, str, str, str]] = [
    (
        "bb-bags-collections-check",
        "Check Bags",
        "/l/womens-bags/check/",
        "bags",
        "bb-bags-collections",
    ),
    (
        "bb-bags-collections-check-men",
        "Check Bags (Men)",
        "/l/mens-bags/check/",
        "bags",
        "bb-bags-collections",
    ),
    (
        "bb-bags-collections-cotswolds",
        "Cotswolds",
        "/l/womens-bags/cotswolds/",
        "bags",
        "bb-bags-collections",
    ),
    (
        "bb-bags-collections-highlands",
        "Highlands",
        "/l/womens-bags/highlands/",
        "bags",
        "bb-bags-collections",
    ),
    (
        "bb-bags-collections-horseshoe",
        "Horseshoe",
        "/l/womens-bags/horseshoe/",
        "bags",
        "bb-bags-collections",
    ),
    (
        "bb-bags-collections-bloomsbury",
        "Bloomsbury",
        "/l/womens-bags/bloomsbury/",
        "bags",
        "bb-bags-collections",
    ),
    (
        "bb-bags-collections-b-clip",
        "B Clip",
        "/l/womens-bags/b-clip/",
        "bags",
        "bb-bags-collections",
    ),
    (
        "bb-bags-collections-margate",
        "Margate",
        "/l/womens-bags/margate/",
        "bags",
        "bb-bags-collections",
    ),
]
