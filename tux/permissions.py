import configparser
import logging

config = configparser.ConfigParser()
config.read("config/settings.ini")
feature_permissions_section = config["Feature_Permissions"]


def check_permission(role, command):
    command_permissions = feature_permissions_section.get(command, None)

    if command_permissions is not None:
        required_permissions = command_permissions.split(",")
        return role in required_permissions
    else:
        logging.warning(f"Command '{command}' not found in the configuration.")
        return False
