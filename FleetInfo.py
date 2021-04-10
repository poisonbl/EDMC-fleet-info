
import tkinter as tk
from tkinter import ttk
import pathlib
import json
import logging
import l10n
import functools
import os
#import math
import re
import monitor

import plug

from ttkHyperlinkLabel import HyperlinkLabel
import myNotebook as nb

from typing import Optional, Tuple, Dict, List, Any
from config import appname, config
from companion import ship_map
#from edmc_data import ship_name_map as ship_map

_ = functools.partial(l10n.Translations.translate, context=__file__)
plugin_name = os.path.basename(os.path.dirname(__file__))
logger = None

class FleetInfo():
    def __init__(self, plugin_dir, logger_in):
        global logger
        logger = logger_in
        self.parent = None
        self.is_beta: bool = False
        self.plugin_dir = plugin_dir
        self.filename: str = "edmc-fleet-info-data.json"
        self.filepath = os.path.join(plugin_dir, self.filename)
        self.label: Optional[HyperlinkLabel] = None
        self.shiplist: Optional[tk.OptionMenu] = None
        self.selectedship: Optional[tk.StringVar] = None
        self.tracevar = None
        self.shipdata: Optional[Dict[str, Dict[str, Any]]] = {"0":{"Name":"Loading","loadout":None}}
        self.shipnames: List = ["0: Loading..."]
        self.lastship: str = self.shipnames[0]

    # Build the UI and hook the selection event
    def setup_gui(self, parent) -> Tuple[HyperlinkLabel,tk.OptionMenu]:
        self.parent = parent
        self.selectedship = tk.StringVar(parent)
        self.label = HyperlinkLabel(parent, url="http://coriolis.io", name='shipyardlink', text=f'{_("Shipyard")}:')
        self.shiplist = tk.OptionMenu(parent, self.selectedship, self.shipnames[0], *self.shipnames)
        self.tracevar = self.selectedship.trace_add("write",self.updateshipurl)
        self.loadshipdata()
        return (self.label,self.shiplist)

    # Update the hyperlink underneath the "Shipyard:" label any time the selection changes
    def updateshipurl(self, name=None, *args) -> None:
        self.lastship = self.selectedship.get()
        shipid = ""
        match = re.match(r'^\s*(\d+):',self.selectedship.get())
        if match:
            shipid = match.group(1)
        if shipid and self.shipdata[shipid] and self.shipdata[shipid]["loadout"]:
            url = plug.invoke(config.get('shipyard_provider'), 'EDSY', 'shipyard_url', self.shipdata[shipid]["loadout"], self.is_beta)
            self.label.configure(url=url)
        else:
            logger.debug("No loadout for {ship}".format(ship=self.lastship))
            self.label.configure(url="http://coriolis.io")

    # Load in fleet data from file
    def loadshipdata(self) -> None:
        self.shipdata = {0:{"Name":"Loading...","loadout":None}}
        try:
            logger.debug(f'Loading ship data from {self.filepath!r}')
            with open(self.filepath, mode='r', encoding='utf-8') as shipsfile:
                self.shipdata = json.load(shipsfile)
                close(shipsfile)
        except Exception as e:
            pass
        if not isinstance(self.shipdata,dict):
            self.shipdata = {0:{"Name":"Loading...","loadout":None}}
        self.updateships()

    # Write fleet data out to file, done every time it changes
    def saveshipdata(self) -> None:
        try:
            logger.trace(f'Saving ship data to {self.filepath!r}')
            with open(self.filepath, mode='w', encoding='utf-8') as shipsfile:
                json.dump(self.shipdata, shipsfile, indent=2)
                close(shipsfile)
        except Exception as e:
            pass

    # Update the loadout for the current ship from a Loudout journal entry
    def updateloadout(self, entry: Dict[str, Any], state: Dict[str,Any]) -> None:
        logger.trace("Updating loadout")
        shipid = str(entry["ShipID"])
        n: str = ""
        if shipid in self.shipdata.keys():
            n = self.shipdata[shipid]["Name"]
        if "ShipName" in state.keys() and state["ShipName"]:
            n = state["ShipName"]
        elif "ShipName" in state.keys() and not n:
            n = ship_map.get(state["ShipType"], state["ShipType"])
        self.shipdata[shipid]["Name"] = n
        self.shipdata[shipid]["loadout"] = entry
        self.updateships()
        self.saveshipdata()

    # Update the list of all ships, local and remote, preserving loadouts for
    # any that have them. Clears out ships that aren't found in the StoredShips
    # journal entry/current ship state data
    def updateshipyard(self, entry: Dict[str, Any], state: Dict[str,Any]) -> None:
        logger.trace("Updating Shipyard")
        keep: List[Optional[int]] = []

        # Update the current ship
        shipid: str = str(state["ShipID"])
        loadout: Optional[Dict[str, Any]] = None
        n: str = ""
        if shipid in self.shipdata.keys():
            loadout = self.shipdata[shipid]["loadout"]
            n = self.shipdata[shipid]["Name"]
        if "ShipName" in state.keys() and state["ShipName"]:
            n = state["ShipName"]
        elif "ShipType" in state.keys() and (not n or n == state["ShipType"]):
            n = ship_map.get(state["ShipType"].lower(), state["ShipType"])
        elif not n:
            n = "Unknown"
            logger.debug("Unknown Ship Name/Type")
            logger.debug(s)
        self.shipdata[shipid] = {"Name":n,"loadout":loadout}
        keep.append(shipid)

        # Update all local and remote ships from the journal entry
        for s in (entry["ShipsHere"] + entry["ShipsRemote"]):
            loadout = None
            shipid = str(s["ShipID"])
            n = ""
            if shipid in self.shipdata.keys():
                loadout = self.shipdata[shipid]["loadout"]
                n = self.shipdata[shipid]["Name"]
            if "Name" in s.keys() and s["Name"]:
                n = s["Name"]
            elif "ShipType" in s.keys() and (not n or n == s["ShipType"]):
                n = ship_map.get(s["ShipType"].lower(), s["ShipType"])
            elif not n:
                n = "Unknown"
                logger.debug("Unknown Ship Name/Type")
                logger.debug(s)
            self.shipdata[shipid] = {"Name":n,"loadout":loadout}
            keep.append(shipid)

        # Remove any extra entries that the shipyard + state didn't contain
        self.shipdata = dict([(k,v) for k,v in self.shipdata.items() if k in set(keep)])
        self.updateships()
        self.saveshipdata()

    # Update the "id: Name" list used for the menu
    def updateships(self) -> None:
        logger.trace("Updating ship menu")
        self.shipnames.clear()
        self.shiplist['menu'].delete(0,'end')
        width = max(len(k) for k in self.shipdata.keys())
        for k in self.shipdata.keys():
            s: str = "{k: >{width}}: {n}".format(k=k,n=self.shipdata[k]["Name"],width=width)
            self.shipnames.append(s)
        self.shipnames.sort()
        for s in self.shipnames:
            self.shiplist['menu'].add_command(label=s, command=tk._setit(self.selectedship, s))
        if self.lastship in self.shipnames:
            self.selectedship.set(self.lastship)
        else:
            self.selectedship.set(self.shipnames[0])
        self.lastship = " "
        self.updateshipurl()
