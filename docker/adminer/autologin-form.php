<?php
/**
 * Adminer plugin for filling and/or auto-submitting the login form.
 *
 * This class allows you to pre-fill the Adminer login form fields
 * with predefined credentials, and optionally auto-submit
 * the form to perform an automatic login.
 *
 * Typical usage: instantiate the class with login parameters and call loginForm().
 *
 * @author Paul BOREL <paul.borel@gmail.com>
 * Forked and adapted for Tux project
 */

class AdminerAutoLoginForm {

    /**
     * @var array Associative array with login parameters: system, server, name, pass, database.
     */
    private $params;

    /**
     * @var bool Indicates whether the form should be automatically submitted after filling.
     */
    private $autoSubmit;

    /**
     * Initializes the plugin to fill (and optionally auto-submit) the Adminer login form.
     *
     * The $params keys can be:
     * - system : (string) database driver type. Possible values:
     *   - "server" (MySQL)
     *   - "sqlite" (SQLite3)
     *   - "sqlite2" (SQLite2)
     *   - "pgsql" (PostgreSQL)
     *   - "oracle" (Oracle)
     *   - "mssql" (MS SQL)
     *   - "firebird" (Firebird alpha)
     *   - "simpledb" (SimpleDB)
     *   - "mongo" (MongoDB)
     *   - "elastic" (Elasticsearch)
     * - server : (string) SQL server address/name, default ""
     * - name : (string) SQL username, default ""
     * - pass : (string) password, default ""
     * - database : (string) database name, default ""
     *
     * @param array $params Associative array of login parameters.
     * @param bool $autoSubmit Whether to automatically submit the form after filling it (default true).
     */
    public function __construct(array $params = [], $autoSubmit = null) {
        $defaults = [
            'system' => $_ENV['ADMINER_DEFAULT_SYSTEM'] ?? 'pgsql',
            'server' => $_ENV['ADMINER_DEFAULT_SERVER'] ?? '',
            'name' => $_ENV['ADMINER_DEFAULT_NAME'] ?? '',
            'pass' => $_ENV['ADMINER_DEFAULT_PASS'] ?? '',
            'database' => $_ENV['ADMINER_DEFAULT_DATABASE'] ?? '',
        ];

        $autoSubmit = $autoSubmit ?? (($_ENV['ADMINER_AUTOLOGIN_AUTOSUBMIT'] ?? 'true') === 'true');
        $this->params = array_merge($defaults, $params);
        $this->autoSubmit = $autoSubmit;
    }

    function name() {
        return null;
    }

    /**
     * Outputs JavaScript code to pre-fill and/or auto-submit the Adminer login form.
     *
     * The script is output only if the URL parameters do not already contain
     * the login information (driver, username, db).
     *
     * @return null
     */
    public function loginForm() {
        // Check if we're already logged in (URL contains driver, username, or db parameters)
        $empty = empty($_GET['driver'] ?? '') &&
                 empty($_GET['username'] ?? '') &&
                 empty($_GET['db'] ?? '');

        if ($empty) {
            $fields = [
                'auth[server]' => $this->params['server'],
                'auth[username]' => $this->params['name'],
                'auth[password]' => $this->params['pass'],
                'auth[db]' => $this->params['database']
            ];
?>
<script<?= Adminer\nonce(); ?>>
document.addEventListener("DOMContentLoaded", function() {
    // Select the driver in the dropdown
    var dr = document.querySelector('option[value="<?= htmlspecialchars($this->params['system']) ?>"]');
    if(dr) dr.selected = true;

    // Auto-fill the form fields
<?php foreach($fields as $name => $value): if($value): ?>
    var el = document.querySelector('input[name="<?= htmlspecialchars($name) ?>"]');
    if(el && el.value.trim() === "") el.value = "<?= addslashes($value) ?>";
<?php endif; endforeach; ?>

    // Automatically submit the form if enabled
<?php if($this->autoSubmit): ?>
    var btn = document.querySelector('input[type="submit"]');
    if(btn) btn.click();
<?php endif; ?>
});
</script>
<?php
        }
        return null;
    }
}

// Return plugin instance for Adminer plugin system
return new AdminerAutoLoginForm();
