# ===========================================================================
# Script name: config_loader.py
# Purpose:     Loads and validates config.json from the repository root.
#              All scripts in script_modules import this module to resolve
#              environment-specific file paths instead of hardcoding them.
#
#              config.json is gitignored — it is never committed.
#              If config.json is absent, this module generates a skeleton
#              file with placeholder values and raises an error so the user
#              knows to fill it in before running any tool.
#
# Created: 2026-07-22
# ===========================================================================

import json
import os

# ---------------------------------------------------------------------------
# Resolve the repository root (one level above script_modules/)
# ---------------------------------------------------------------------------
_SCRIPT_MODULES_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_MODULES_DIR)
_CONFIG_PATH = os.path.join(_REPO_ROOT, "config.json")

# ---------------------------------------------------------------------------
# Placeholder skeleton written when config.json is missing.
# Values that start with "<" and end with ">" are placeholders the user must
# replace.  No real network paths ever appear in this source file.
# ---------------------------------------------------------------------------
_SKELETON = {
    "_comment": (
        "config.json — LOCAL CONFIGURATION — do NOT commit this file. "
        "It is listed in .gitignore. "
        "Replace every <placeholder> value with the real path for your environment."
    ),
    "check_in_dataset": {
        "_comment": "Paths used by check_in_dataset.py and the CheckInDataset toolbox tool.",
        "update_mgmt_base": "<UNC or local path to the UpdateManagement root folder>"
    },
    "compare_num_records": {
        "_comment": (
            "Paths used by compare_number_of_records_staging_vs_bcgw.py and the "
            "CompareNumRecords toolbox tool."
        ),
        "staging_base": "<UNC or local path to the staging area base folder (contains the dataset GDBs)>",
        "bcgw_sde": "<Full path to the BCGW .sde connection file>",
        "dataset_paths": {
            "_comment": (
                "Sub-paths appended to staging_base to reach each feature class. "
                "These are data-model paths, not secrets, but are kept here so that "
                "any future GDB rename only requires a config edit, not a code change."
            ),
            "ogma_legal":      "old_growth_management_area_bc.gdb\\old_growth_management_area_albers\\old_growth_management_area_legal_bc_poly",
            "ogma_non_legal":  "old_growth_management_area_bc.gdb\\old_growth_management_area_albers\\old_growth_management_area_non_legal_bc_poly",
            "lu":              "landscape_unit_bc.gdb\\landscape_unit_albers\\landscape_unit_poly",
            "slrp_boundary":   "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_boundary_bc_poly",
            "slrp_legal_poly_CAR":        "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_CAR_poly",
            "slrp_legal_poly_FSJ":        "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_FSJ_poly",
            "slrp_legal_poly_KAM":        "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_KAM_poly",
            "slrp_legal_poly_KOR":        "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_KOR_poly",
            "slrp_legal_poly_NAN":        "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_NAN_poly",
            "slrp_legal_poly_PRG":        "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_PRG_poly",
            "slrp_legal_poly_SKE":        "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_SKE_poly",
            "slrp_legal_poly_SUR":        "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_SUR_poly",
            "slrp_legal_line_CAR":        "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_CAR_line",
            "slrp_legal_line_FSJ":        "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_FSJ_line",
            "slrp_legal_line_KAM":        "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_KAM_line",
            "slrp_legal_line_KOR":        "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_KOR_line",
            "slrp_legal_line_NAN":        "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_NAN_line",
            "slrp_legal_line_PRG":        "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_PRG_line",
            "slrp_legal_line_SKE":        "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_SKE_line",
            "slrp_legal_line_SUR":        "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_SUR_line",
            "slrp_legal_point_CAR":       "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_CAR_point",
            "slrp_legal_point_FSJ":       "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_FSJ_point",
            "slrp_legal_point_KAM":       "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_KAM_point",
            "slrp_legal_point_KOR":       "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_KOR_point",
            "slrp_legal_point_NAN":       "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_NAN_point",
            "slrp_legal_point_PRG":       "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_PRG_point",
            "slrp_legal_point_SKE":       "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_SKE_point",
            "slrp_legal_point_SUR":       "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_legal_SUR_point",
            "slrp_non_legal_poly_CAR":    "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_CAR_poly",
            "slrp_non_legal_poly_FSJ":    "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_FSJ_poly",
            "slrp_non_legal_poly_KAM":    "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_KAM_poly",
            "slrp_non_legal_poly_KOR":    "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_KOR_poly",
            "slrp_non_legal_poly_NAN":    "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_NAN_poly",
            "slrp_non_legal_poly_PRG":    "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_PRG_poly",
            "slrp_non_legal_poly_SKE":    "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_SKE_poly",
            "slrp_non_legal_poly_SUR":    "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_SUR_poly",
            "slrp_non_legal_line_CAR":    "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_CAR_line",
            "slrp_non_legal_line_FSJ":    "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_FSJ_line",
            "slrp_non_legal_line_KAM":    "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_KAM_line",
            "slrp_non_legal_line_KOR":    "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_KOR_line",
            "slrp_non_legal_line_NAN":    "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_NAN_line",
            "slrp_non_legal_line_PRG":    "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_PRG_line",
            "slrp_non_legal_line_SKE":    "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_SKE_line",
            "slrp_non_legal_line_SUR":    "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_SUR_line",
            "slrp_non_legal_point_CAR":   "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_CAR_point",
            "slrp_non_legal_point_FSJ":   "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_FSJ_point",
            "slrp_non_legal_point_KAM":   "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_KAM_point",
            "slrp_non_legal_point_KOR":   "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_KOR_point",
            "slrp_non_legal_point_NAN":   "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_NAN_point",
            "slrp_non_legal_point_PRG":   "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_PRG_point",
            "slrp_non_legal_point_SKE":   "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_SKE_point",
            "slrp_non_legal_point_SUR":   "strategic_land_resource_plan_bc.gdb\\strategic_land_resource_plan_albers\\slrp_planning_feature_non_legal_SUR_point"
        }
    },
    "zip_year_archives": {
        "_comment": "Paths used by zip_year_archives.py.",
        "root_dir": "<UNC or local path to the root folder to recursively scan for .gdb folders to zip>"
    }
}

# ---------------------------------------------------------------------------
# Module-level cache — loaded once per Python session
# ---------------------------------------------------------------------------
_config_cache = None


def _load():
    """Load config.json from the repo root. Generates a skeleton and raises
    FileNotFoundError if the file is missing."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    if not os.path.isfile(_CONFIG_PATH):
        # Write the skeleton so the user has a starting point
        with open(_CONFIG_PATH, "w", encoding="utf-8") as fh:
            json.dump(_SKELETON, fh, indent=4)
        raise FileNotFoundError(
            f"config.json was not found at:\n  {_CONFIG_PATH}\n"
            "A skeleton file has been created at that location.\n"
            "Open it, replace every <placeholder> value with the real path for\n"
            "your environment, then re-run the tool."
        )

    with open(_CONFIG_PATH, "r", encoding="utf-8") as fh:
        _config_cache = json.load(fh)

    return _config_cache


def get(section, key):
    """Return a single string value from config.json.

    Parameters
    ----------
    section : str  Top-level key in config.json (e.g. 'check_in_dataset').
    key     : str  Key within that section (e.g. 'update_mgmt_base').

    Raises
    ------
    KeyError        If section or key is absent.
    ValueError      If the value is still a placeholder (<…>).
    FileNotFoundError  If config.json does not exist.
    """
    cfg = _load()
    if section not in cfg:
        raise KeyError(
            f"Section '{section}' not found in config.json ({_CONFIG_PATH}).\n"
            "Add this section or check for a typo."
        )
    section_data = cfg[section]
    if key not in section_data:
        raise KeyError(
            f"Key '{key}' not found in section '{section}' of config.json ({_CONFIG_PATH}).\n"
            "Add this key or check for a typo."
        )
    value = section_data[key]
    if isinstance(value, str) and value.startswith("<") and value.endswith(">"):
        raise ValueError(
            f"config.json key '{section}.{key}' still contains a placeholder value:\n"
            f"  {value}\n"
            f"Edit {_CONFIG_PATH} and replace it with the real path."
        )
    return value


def get_section(section):
    """Return an entire section dict from config.json.

    Parameters
    ----------
    section : str  Top-level key in config.json.

    Raises
    ------
    KeyError        If section is absent.
    FileNotFoundError  If config.json does not exist.
    """
    cfg = _load()
    if section not in cfg:
        raise KeyError(
            f"Section '{section}' not found in config.json ({_CONFIG_PATH}).\n"
            "Add this section or check for a typo."
        )
    return cfg[section]


def get_dataset_path(staging_base, key):
    """Build a full dataset path by joining staging_base with the relative
    sub-path stored at compare_num_records.dataset_paths.<key>.

    Parameters
    ----------
    staging_base : str  The staging root folder path (already validated by caller).
    key          : str  A key from compare_num_records.dataset_paths.

    Returns
    -------
    str  Full path to the feature class.

    Raises
    ------
    KeyError   If key is absent from dataset_paths.
    """
    dataset_paths = get_section("compare_num_records")["dataset_paths"]
    if key not in dataset_paths:
        raise KeyError(
            f"Dataset path key '{key}' not found in "
            f"compare_num_records.dataset_paths in config.json ({_CONFIG_PATH})."
        )
    return os.path.join(staging_base, dataset_paths[key])
