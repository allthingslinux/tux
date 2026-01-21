---
title: For Developers
description: Frequently asked questions for Tux developers.
parent: FAQ
icon: material/help-circle-outline
---

# For Developers

## Can I add my own commands or plugins?

Yes. Self-hosters can add [plugins](../developer/concepts/core/plugins.md) in `src/tux/plugins/`. Plugins are loaded automatically and have the same capabilities as built-in modules (database, config, hot reload).

## Do I need Docker to develop Tux?

No. You can develop Tux without Docker. However, it is recommended to use Docker for the simplest setup in regards to database support.
