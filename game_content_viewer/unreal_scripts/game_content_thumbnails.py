"""A utility script for generating asset thumbnails from Unreal."""

import imp
from pathlib import Path

import unreal

file_path = (Path(__file__).parents[1] / "game_content_utils" / "config_file.py").as_posix()
config_file = imp.load_source("config_file", file_path)

THUMBNAILS_SAVE_FOLDER = config_file.THUMBNAILS_SAVE_FOLDER
UE_FOLDER_PATH_VALUE = config_file.load_saver()


def get_thumbnail(ue_folder_path: str, save_folder_path: str | Path) -> None:
    """Exports thumbnails for Unreal assets into the specified folder.

    Args:
        ue_folder_path: The Unreal project folder path containing assets.
            (ex. "/Game/StarterContent/")
        save_folder_path: The local filesystem path or Path object where thumbnails are saved.

    """
    save_folder_path.mkdir(parents=True, exist_ok=True)
    full_object_paths = unreal.EditorAssetLibrary.list_assets(ue_folder_path, recursive=True)
    asset_paths = [get_package_name(path) for path in full_object_paths]
    for asset_path in asset_paths:
        unreal.log(f"Processing asset: {asset_path}")
        asset_listed = unreal.EditorAssetLibrary.find_asset_data(asset_path)
        asset_name = str(asset_listed.asset_name)

        full_path_name = str(asset_listed.get_export_text_name())
        save_file_path = Path(save_folder_path) / str(asset_name + "_Thumbnail.jpg")

        if hasattr(unreal, "ThumbnailExporter"):
            unreal.log("ThumbnailExporter detected in Python.")

            unreal.ThumbnailExporter.export_thumbnail_as_png(
                str(full_path_name),
                str(save_file_path),
            )

            unreal.log(f"Thumbnail saved to: {save_folder_path}")
        else:
            unreal.log_warning("ThumbnailExporter plugin is not loaded.")


def get_package_name(object_path: str) -> str:
    """Extract just the package name from a full object path.
    Avoids error warning in Unreal 5.4.

    Args:
        object_path: The full object path. (ex. "/Game/Path/AssetName.AssetName")

    Returns:
        The package_name (ex. "/Game/Path/AssetName")

    """
    if "." in object_path:
        # split on the last dot to separate package name from object name
        return object_path.rsplit(".", 1)[0]
    return object_path  # return unchanged if more than one dot


if __name__ == "__main__":
    get_thumbnail(UE_FOLDER_PATH_VALUE, THUMBNAILS_SAVE_FOLDER)
