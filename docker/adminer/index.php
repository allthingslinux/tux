<?php
/**
 * Tux Adminer Auto-Login Index
 *
 * This file provides automatic login functionality for Adminer
 * in development environments. In production, it falls back to
 * manual login for security.
 */

// Only auto-login in development environments
if (getenv('ADMINER_AUTO_LOGIN') === 'true' && empty($_GET)) {
  // Pre-fill login form with database connection details
  $_POST['auth'] = [
    'server' => getenv('ADMINER_DEFAULT_SERVER') ?: 'tux-postgres',
    'username' => getenv('ADMINER_DEFAULT_USERNAME') ?: 'tuxuser',
    'password' => getenv('ADMINER_DEFAULT_PASSWORD') ?: 'tuxpass',
    'driver' => getenv('ADMINER_DEFAULT_DRIVER') ?: 'pgsql',
    'db' => getenv('ADMINER_DEFAULT_DB') ?: 'tuxdb',
  ];
}

// Include the main Adminer application
include './adminer.php';
