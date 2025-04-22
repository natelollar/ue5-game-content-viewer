## UE5 Game Content Viewer
Inventory Unreal assets from the `Content/` folder (a.k.a. `Game/`).
- Adds this inventory data to a sqlite database file to be viewed with the custom PySide6 UI.
- CSV output is also available for queried data.

Tested with:
- UE 5.5, 5.4
- Python 3.11.9, 3.11.8
- Windows 11

Download `Game Content Viewer` tool:
- Directly download repository from GitHub or install with git command line. 
    - `git clone github.com/natelollar/ue5-game-content_viewer`
- Place the `ue5-game-content-viewer` folder in a preferred location.
    - Unzip first if directly downloaded from GitHub.
- Install Python .venv or use regular Python install.
    - Install pip requirments listed in `pyproject.toml`.
        - Ruff install is optional.  Helps with formatting.
    - Optionally, use the `venv_install.cmd` if you have Astral's UV installed.
        - Double click this command file in Windows Explorer to install the .venv
            and pip packages in one go.
        - UV finds the pip requirements in the `pyproject.toml`.
        - https://docs.astral.sh/uv/

Launch tool:
- From the downloaded `ue5-game-content-viewer` folder
    launch `main.py` via Python to access the Game Content Viewer UI.

Unreal remote connection:
- Copy the `Python/` folder from `support_files/Content/Python`
    to your Unreal project's `Content/` folder `/Content/Python`.
- Unreal will automatically trigger `init_unreal.py` on launch, 
    which will trigger the `unreal_tcp_server.py` file 
    and open up an Unreal port for remote connection.
- Remote connection is needed to fully utilize this tool.

Thumbnail Plugin:
- Add the thumbnail plugin folder `ThumbnailExporter/` 
    to your Unreal project `Plugins/` folder `UnrealProjectName/Plugins/ThumbnailExporter/`.
- This allows Unreal to export thumbnails.
- Needed for the `Refresh Thumbnails` button.
- Allows asset thumbnails to appear below info window after queried.

Launch Unreal via the UI:
- The `UE5` button in the top right of the UI launches a custom Unreal project.
- Update the file paths in `launch_ue.exe` to launch a custom project.
    - The first path is the Unreal `.exe` file.
    - The second path is the `.uproject` file.

### UI Elements
Top Toolbar:
- Search Field
    - A search field text input to limit what is shown in the spreadsheet view.
        - The dropdown determines what column is being searched in.

- Reload Spreadsheet
    - A button to reload the spreadsheet after refreshing the sqlite database.

- Refresh Database
    - A button that sends the `game_content_scanner.py` script to Unreal via remote connection.
        - This script queries the asset metadata and creates a sqlite .db file for it.
    - Limit the inventory query by specifying the folder in the text field next to the button.

- Refresh Thumbnails
    - Gets the thumbnail for each Unreal asset in the query.
        - Adds thumbnails to `data/thumbnails` folder for viewing in the UI.
    - This button takes longer as it needs to load in each asset.
    - Use with caution on large projects as loading in assets can fill up memory.
        - Get thumbnails for specific folders at a time if project is too large.
    - Thumbnails may need to be refreshed multiple times to load in the full resolution.
        - Subequent refreshes during a single Unreal session should go much faster.
    - This thumbnail query uses the same text field as the refresh database button
        to limit query.


Center Windows:
- Spreadsheet View
    - The spreadshet window view shows all the data from `data/game_content.db`.

- Info Window
    - To the right is the info window displaying more data for the selected object row.
    - The info window displays the same info vertically 
        and also info parsed from the `tag_values` column.
    - The `Open File Location` button at the bottom of the info window
        opens the folder location where the selected asset is.

Bottom Toolbar:
- Output CSV
    - This button outputs .csv files based on the tables in `game_content.db`.
    - These .csv files are outputed alongside the .db file in the `data/` folder.
    - The `game_content.csv` can be helpful if user needs to view data in another app.

- Summary Bar
    - The bottom bar shows a summary of how many assets are in each class type
        and total number of assets. 

