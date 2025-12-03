*[ABC]: Abstract Base Class - defines interface without implementation
*[Access Token]: Temporary credential for API access
*[Application Command]: Discord's modern command system including slash commands
*[Background Task]: A coroutine that runs continuously in the background using @tasks.loop
*[Bearer Token]: Authorization header format for API requests
*[Bucket]: Rate limiting category for similar requests
*[CLI]: Command Line Interface - A text-based interface for interacting with programs
*[Check]: A predicate function that determines if a user can run a command
*[Client ID]: Unique identifier for Discord applications
*[Client Secret]: Private key for OAuth2 authentication
*[Client User]: The bot's own user object containing ID, username, and other properties
*[Cog]: A Python class that organizes commands, listeners, and state into a single module
*[Command Group]: A collection of related slash commands under a parent name
*[CommandTree]: A special class that holds all application command state and functionality
*[Context Menu]: Right-click commands available on users or messages
*[Context]: The invocation context containing information about how a command was executed
*[Converter]: A function or class that transforms user input into a specific type
*[Cooldown]: A time restriction preventing command spam
*[Decorator]: A Python feature that modifies or wraps functions, used extensively in Discord.py
*[Dot-Qualified]: Python import syntax using dots for nested modules, like plugins.hello
*[Entry Point]: A required function in an extension, typically setup() and optionally teardown()
*[Ephemeral]: A response visible only to the user who triggered the interaction
*[Event Loop]: Core asyncio component that manages async operations
*[Event]: A Discord gateway event that bots can listen for and respond to
*[Extension]: A Python module that can be loaded/unloaded dynamically to add cogs to a bot
*[Flag]: A named parameter in FlagConverter for complex command interfaces
*[Gateway]: Discord's WebSocket connection for real-time communication
*[Gateway]: Discord's WebSocket connection for real-time events
*[Global Commands]: Application commands available across all guilds where the bot is present
*[Grant Type]: OAuth2 flow method (authorization code, client credentials)
*[Greedy]: A converter that consumes as many arguments as possible
*[Guild Commands]: Application commands registered to specific guilds for faster testing
*[Guild]: Discord's term for a server
*[Hybrid Command]: A command that works as both text and slash command
*[Intent]: A permission that allows bots to receive specific types of events
*[Intents]: Permissions that control which events a bot can receive from Discord
*[Inter-Cog Communication]: Using bot.get_cog() to share data between different cogs
*[Interaction]: Discord's response system for slash commands and components
*[JSON]: JavaScript Object Notation - A lightweight data interchange format
*[Keyword-Only]: Parameters that must be specified by name, not position
*[Listener]: A method that responds to Discord events, marked with @commands.Cog.listener()
*[Literal]: A type hint restricting values to specific literal options
*[Messageable]: An ABC for objects that can send messages (channels, users, etc.)
*[Metaclass]: A Python class that defines how other classes are created, used by CogMeta
*[Migration]: A script that updates the database schema when upgrading to a new version
*[Modal]: A form-like interface in Discord that allows users to input data
*[Namespace]: An object containing command parameter values
*[OAuth2]: Authorization protocol for Discord integrations
*[OS]: Operating System - Software that manages computer hardware and software resources
*[Optional]: A type hint indicating a parameter can be None or omitted
*[Parameter]: An argument that a command function accepts from user input
*[Payload]: Raw data received from Discord's API
*[Plugin]: An extension that adds functionality to the bot without modifying core code
*[Positional]: Parameters that must be provided in a specific order
*[Presence]: A user's online status and activity information
*[Privileged Intent]: Special intents requiring explicit approval in Discord Developer Portal
*[RAM]: Random Access Memory - Computer memory used for temporary data storage
*[Raw Event]: Low-level Discord events that bypass the cache
*[Redirect URI]: Callback URL for OAuth2 authentication
*[Refresh Token]: Long-term credential for renewing access tokens
*[Registration]: The process of adding a cog to a bot using Bot.add_cog()
*[Runtime]: The period when a program is executing, allowing dynamic loading/unloading
*[SQL]: Structured Query Language - A language for managing databases
*[SSH]: Secure Shell - A protocol for secure remote access to computers
*[SSL]: Secure Sockets Layer - A security protocol for encrypted communication
*[Scope]: Permission level requested during OAuth2 flow
*[Service]: A layer of abstraction that handles business logic and data operations
*[Setup Function]: An async function called when an extension is loaded, takes bot as parameter
*[Setup Hook]: An async method called during bot startup for initialization tasks
*[Shard]: A connection partition for large bots across multiple processes
*[Shard]: A connection to Discord's gateway for large bots across multiple processes
*[Slash Command]: Discord's built-in command system with UI integration
*[Status]: Online state (online, idle, dnd, offline)
*[Subcommand]: A command nested under a command group
*[Sync]: The process of uploading application commands to Discord's servers
*[TLS]: Transport Layer Security - The successor to SSL for secure communication
*[TOML]: Tom's Obvious, Minimal Language - A configuration file format
*[Task Loop]: A decorator that repeatedly executes a function at specified intervals
*[Teardown Function]: An async function called when an extension is unloaded for cleanup
*[Tree]: The structure that holds all application command state
*[UUID]: Universally Unique Identifier - A unique identifier standard
*[Union]: A type hint allowing multiple possible types for a parameter
*[VPS]: Virtual Private Server - A virtualized server environment
*[Variable]: Parameters that accept multiple arguments using*args syntax
*[View]: An interactive Discord component that can contain buttons and other elements
*[Webhook]: A way for external services to send data to Discord channels
*[XP]: Experience Points - A system for tracking user activity and engagement
*[YAML]: YAML Ain't Markup Language - A human-readable data serialization format
