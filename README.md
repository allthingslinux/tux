# Extensions

This is one of the more new/basic features of Tux, however it is a very powerful one. This will let you add custom commands to Tux without having to modify the code. This is done by creating a new file in the `tux/extensions` folder. The file is just a regular Discord.py cog.

At the end of the day it is about the same as just adding a cog to the bot manually, you can also do this if you so wish (the src/ folder is docker mounted so modifications will be reflected in the container as well).

> [!TIP]
> We scan subdirectories so you can use git submodules to add extensions!

## Limitations

Unfortunately using extensions does come with some limitations:

- Everything is in the same category (Extensions)
- You cannot add your own data to the database schema (unless you want to modify the code), a solution might be added in the future.
- You cannot add extra packages (unless you modify the code), a solution might be added in the future.
