
import tkinter as tk
import logging
import os

from FleetInfo import FleetInfo

from ttkHyperlinkLabel import HyperlinkLabel
from typing import Optional, Tuple, Dict, Any
from config import appname

plugin_name = os.path.basename(os.path.dirname(__file__))
logger = logging.getLogger(f'{appname}.{plugin_name}')

fleet_info: Optional[FleetInfo] = None

def plugin_start3(plugin_dir: str) -> str:
    global fleet_info
    fleet_info = FleetInfo(plugin_dir, logger)
    logger.debug('Plugin loaded')
    return plugin_name

def plugin_stop() -> None:
    pass

def prefs_changed(cmdr: str, is_beta: bool) -> None:
    pass

def plugin_app(parent) -> Tuple[HyperlinkLabel,tk.OptionMenu]:
    global fleet_info
    return fleet_info.setup_gui(parent)

def journal_entry(
    cmdr: str, is_beta: bool, system: str, station: str, entry: Dict[str, Any], state: Dict[str, Any]
) -> None:
    global fleet_info
    fleet_info.is_beta = is_beta
    if entry['event'] in set(['Loadout', 'StoredShips']):
        if entry['event'] == "StoredShips":
            fleet_info.updateshipyard(entry, state)
        elif entry['event'] == "Loadout":
            fleet_info.updateloadout(entry, state)
