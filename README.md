# EDMC Fleet Information Plugin

This plugin for [EDMarketConnector](https://github.com/EDCD/EDMarketConnector) captures the loadout of each ship when it's active. This allows pulling up the ship build in [Coriolis](https://coriolis.io) or [EDSY](https://edsy.org/) (whichever is selected for use in EDMC) for all ships, instead of only the active one (the plugin does *not* currently support the "Use alternate URL method" configuration option).

Opening the shipyard will update the list of owned ships (local and remote), while loadouts only update when a loadout journal event is received (game load, exiting outfitting with changes, changing ships).

Data for your fleet is stored in edmc-fleet-info-data.json inside the plugin folder.

## Installation

  * On EDMC's Plugins settings tab press the “Open” button. This reveals the `plugins` folder where EDMC looks for plugins.
  * Download the [latest release](https://github.com/poisonbl/EDMC-fleet-info/releases/latest) of this plugin.
  * Open the `.zip` archive that you downloaded and move the `EDMC-fleet-info` folder contained inside into the `plugins` folder.

  _You will need to re-start EDMC for it to notice the new plugin._
