---
title: For Admins
description: Frequently asked questions for server admins.
parent: FAQ
icon: material/help-circle-outline
---

# For Admins

## How do I configure Tux?

Use `config.json` for app settings (roles, features, limits) and `.env` for secrets and environment-specific values. Use the `/config` command for an interactive [configuration dashboard](../admin/config/index.md).

## Can I change the command prefix?

Yes. You can change the command prefix in `config.json` under `BOT_INFO.PREFIX`.
