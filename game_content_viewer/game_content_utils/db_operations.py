"""Module with operations to help with parsing a sqlite database (.db) file.
Also, has a function to help format a sqlite table into html.
"""

import ast
import json
import sqlite3

from . import config_file

DB_FILE_PATH = config_file.DB_FILE_PATH


def db_get_table(table_name: str) -> list[dict]:
    """Query sql table data.

    Args:
        table_name: The name of the SQL table to query.

    Returns:
        A list of dictionaries representing the table rows.

    """
    sql_conn = sqlite3.connect(DB_FILE_PATH)
    sql_cursor = sql_conn.cursor()
    sql_query = f"SELECT * FROM {table_name}"
    sql_cursor.execute(sql_query)

    column_names = [description[0] for description in sql_cursor.description]
    table_rows = sql_cursor.fetchall()
    table_results = []
    for row in table_rows:
        row_dict = dict(zip(column_names, row, strict=False))
        table_results.append(row_dict)

    sql_cursor.close()
    sql_conn.close()

    return table_results


def db_get_table_row(table_name: str, column_name: str, column_value: str) -> dict:
    """Get table row based on column value.

    Args:
        table_name: The name of the SQL table to query.
        column_name: The column to filter by.
        column_value: The value to match in the specified column.

    Returns:
        A dictionary representing the matched row, with column names as keys.

    """
    sql_conn = sqlite3.connect(DB_FILE_PATH)
    sql_cursor = sql_conn.cursor()
    sql_query = f"SELECT * FROM {table_name} WHERE {column_name} = ?"
    sql_cursor.execute(sql_query, (column_value,))

    column_names = [description[0] for description in sql_cursor.description]

    table_row = sql_cursor.fetchone()
    table_row_dict = dict(zip(column_names, table_row, strict=False))

    sql_cursor.close()
    sql_conn.close()

    return table_row_dict


def get_tag_values(table_row: dict) -> dict:
    """Get tag_values dict from table row.

    Args:
        table_row: A dictionary representing a row from a database table.

    Returns:
        A dictionary parsed from the 'tag_values' field.

    """
    tag_val = table_row.get("tag_values")

    tag_val_dict = ast.literal_eval(tag_val)

    return tag_val_dict


def get_tag_values_dict(tag_values: dict, dict_name: str) -> dict:
    """Get a dictionary from the tag_values, and a value from that dict if needed.

    Args:
        tag_values: A dictionary containing JSON-encoded values.
        dict_name: The key whose value should be extracted and parsed.

    Returns:
        The first dictionary from the parsed JSON list.

    """
    dict = tag_values.get(dict_name)
    return json.loads(dict)[0]


def update_text_display(asset_name: str) -> str:
    """Update the display with selected asset dictionary data.

    Args:
        asset_name: The name of the asset to look up.

    Returns:
        An HTML-formatted string displaying the asset's combined data.

    """
    table_row = db_get_table_row("game_content", "asset_name", asset_name)
    tag_values = get_tag_values(table_row)

    # get dictionaries from tag_values
    tgv_dict_key_list = []
    tgv_dict_list = []
    for key, value in tag_values.items():
        try:
            tgv_dict = json.loads(value)[0]
        except Exception:
            continue
        if isinstance(tgv_dict, dict):
            tgv_dict_key_list.append(key)
            tgv_dict_list.append(tgv_dict)

    # remove keys from display that are being parsed further
    for key in tgv_dict_key_list:
        tag_values.pop(key)
    table_row.pop("tag_values")

    # combined dicts to display
    display_dict = []
    display_dict = table_row | tag_values
    for tgv_dict in tgv_dict_list:
        display_dict.update(tgv_dict)

    html = ""
    grid_clr = "rgb(70,70,70)"
    for key, value in display_dict.items():
        html += f"""<tr>
        <td style='font-size:10pt; font-weight:bold; text-align:right;
            border: 2px solid {grid_clr};'>{key}:</td>
        <td style='padding-left:3px; border: 2px solid {grid_clr};'>{value}</td>
        </tr>\n"""

    return html
