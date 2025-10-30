*[API]: Application Programming Interface - A set of protocols and tools for building software applications
*[CLI]: Command Line Interface - A text-based interface for interacting with programs
*[CPU]: Central Processing Unit - The main processor of a computer
*[CSS]: Cascading Style Sheets - A language for styling web pages
*[DB]: Database - A structured collection of data
*[DNS]: Domain Name System - A system that translates domain names to IP addresses
*[HTML]: HyperText Markup Language - The standard markup language for web pages
*[HTTP]: HyperText Transfer Protocol - The protocol used for web communication
*[HTTPS]: HyperText Transfer Protocol Secure - The secure version of HTTP
*[JSON]: JavaScript Object Notation - A lightweight data interchange format
*[OS]: Operating System - Software that manages computer hardware and software resources
*[RAM]: Random Access Memory - Computer memory used for temporary data storage
*[SQL]: Structured Query Language - A language for managing databases
*[SSH]: Secure Shell - A protocol for secure remote access to computers
*[SSL]: Secure Sockets Layer - A security protocol for encrypted communication
*[TLS]: Transport Layer Security - The successor to SSL for secure communication
*[TOML]: Tom's Obvious, Minimal Language - A configuration file format
*[UI]: User Interface - The visual elements users interact with
*[URL]: Uniform Resource Locator - A web address
*[UUID]: Universally Unique Identifier - A unique identifier standard
*[VM]: Virtual Machine - A software-based computer running inside another computer
*[VPS]: Virtual Private Server - A virtualized server environment
*[YAML]: YAML Ain't Markup Language - A human-readable data serialization format
*[XP]: Experience Points - A system for tracking user activity and engagement
*[Bot]: A Discord bot - An automated program that interacts with Discord servers and users
*[Cog]: A Python class that organizes commands, listeners, and state into a single module
*[Guild]: Discord's term for a server
*[Embed]: A rich message format in Discord that can include images, fields, and formatted text
*[Modal]: A form-like interface in Discord that allows users to input data
*[View]: An interactive Discord component that can contain buttons and other elements
*[Webhook]: A way for external services to send data to Discord channels
*[Starboard]: A feature that automatically posts starred messages to a designated channel
*[Hot Reload]: A development feature that automatically reloads code changes without restarting the bot
*[Migration]: A script that updates the database schema when upgrading to a new version
*[Service]: A layer of abstraction that handles business logic and data operations
*[Plugin]: An extension that adds functionality to the bot without modifying core code
*[Permission]: A setting that controls what actions a user or bot can perform
*[Role]: A Discord permission group that can be assigned to users
*[Namespace]: A container for related code elements, such as commands or configuration options
*[Operation]: A self-hosting term for ongoing maintenance tasks like backups and updates
*[Query]: A request for data from a database or API
*[Tutorial]: A step-by-step guide that teaches users how to accomplish a specific task
*[Feature]: A distinct functionality or capability of the bot, such as XP system or starboard
*[Integration]: A connection between Tux and external services, such as Sentry for error tracking
*[Logging]: The process of recording events and messages for debugging and monitoring purposes
*[Zone]: A timezone setting used for scheduling and time-based features
*[Context]: The invocation context containing information about how a command was executed
*[Converter]: A function or class that transforms user input into a specific type
*[Check]: A predicate function that determines if a user can run a command
*[Decorator]: A Python feature that modifies or wraps functions, used extensively in Discord.py
*[Parameter]: An argument that a command function accepts from user input
*[Annotation]: Python type hints that specify expected parameter types
*[Positional]: Parameters that must be provided in a specific order
*[Keyword-Only]: Parameters that must be specified by name, not position
*[Variable]: Parameters that accept multiple arguments using*args syntax
*[Union]: A type hint allowing multiple possible types for a parameter
*[Optional]: A type hint indicating a parameter can be None or omitted
*[Literal]: A type hint restricting values to specific literal options
*[Greedy]: A converter that consumes as many arguments as possible
*[Flag]: A named parameter in FlagConverter for complex command interfaces
*[Hybrid Command]: A command that works as both text and slash command
*[Slash Command]: Discord's built-in command system with UI integration
*[Application Command]: Discord's modern command system including slash commands
*[Interaction]: Discord's response system for slash commands and components
*[Autocomplete]: A feature that suggests values as users type slash command parameters
*[Attachment]: A file uploaded to Discord that can be processed by commands
*[Member]: A Discord user within a specific server/guild
*[Channel]: A text, voice, or other communication channel in Discord
*[Message]: A text message, embed, or file sent in Discord
*[Invite]: A link that allows users to join a Discord server
*[Emoji]: A custom or Unicode emoji used in Discord
*[Thread]: A sub-conversation within a Discord channel
*[Sticker]: A custom image that can be sent in Discord messages
*[Event]: A Discord gateway event that bots can listen for and respond to
*[Gateway]: Discord's WebSocket connection for real-time events
*[Intent]: A permission that allows bots to receive specific types of events
*[Shard]: A connection to Discord's gateway for large bots across multiple processes
*[Listener]: A method that responds to Discord events, marked with @commands.Cog.listener()
*[Extension]: A Python module that can be loaded/unloaded dynamically to add cogs to a bot
*[Metaclass]: A Python class that defines how other classes are created, used by CogMeta
*[Registration]: The process of adding a cog to a bot using Bot.add_cog()
*[Inspection]: Methods to examine cog properties like commands and listeners
*[State]: Instance variables in a cog that maintain data between command invocations
*[Inter-Cog Communication]: Using bot.get_cog() to share data between different cogs
*[Entry Point]: A required function in an extension, typically setup() and optionally teardown()
*[Setup Function]: An async function called when an extension is loaded, takes bot as parameter
*[Teardown Function]: An async function called when an extension is unloaded for cleanup
*[Dot-Qualified]: Python import syntax using dots for nested modules, like plugins.hello
*[Runtime]: The period when a program is executing, allowing dynamic loading/unloading
*[Reloading]: The process of unloading and loading an extension to apply code changes
*[Persistent View]: A UI view that survives bot restarts by setting timeout=None and custom_id on items
*[Custom ID]: A unique identifier for UI components, max 100 characters, used for persistence
*[Ephemeral]: A response visible only to the user who triggered the interaction
*[Button Style]: Visual appearance of buttons (green, red, grey, blurple, link)
*[CommandTree]: A special class that holds all application command state and functionality
*[Setup Hook]: An async method called during bot startup for initialization tasks
*[Global Commands]: Application commands available across all guilds where the bot is present
*[Guild Commands]: Application commands registered to specific guilds for faster testing
*[Sync]: The process of uploading application commands to Discord's servers
*[Background Task]: A coroutine that runs continuously in the background using @tasks.loop
*[Task Loop]: A decorator that repeatedly executes a function at specified intervals
*[Messageable]: An ABC for objects that can send messages (channels, users, etc.)
*[ABC]: Abstract Base Class - defines interface without implementation
*[Intents]: Permissions that control which events a bot can receive from Discord
*[Privileged Intent]: Special intents requiring explicit approval in Discord Developer Portal
*[Client User]: The bot's own user object containing ID, username, and other properties
*[Object]: A Discord object representing an entity with just an ID for optimization
*[Response]: The initial reply to an interaction, must be sent within 3 seconds
*[Followup]: Additional messages sent after the initial interaction response
*[Timeout]: Duration after which UI components become inactive and stop responding
*[Assert]: A Python statement that checks if a condition is true, used for type narrowing
*[Select]: A dropdown UI component that allows users to choose from multiple options
*[SelectOption]: Individual choices within a Select dropdown
*[Placeholder]: Text shown when no option is selected
*[Callback]: An async method called when a UI component is interacted with
*[Values]: The selected options from a Select dropdown
*[Row]: Horizontal positioning for UI components in a view
*[Label]: Text displayed on UI components
*[Disabled]: State where a UI component cannot be interacted with
*[Type Hinting]: Python annotations that specify expected types
*[Display Avatar]: A user's current avatar image
*[BadArgument]: Exception raised when command argument conversion fails
*[Command Error]: Base exception class for command-related errors
*[Traceback]: Python error information showing the call stack
*[Raw Reaction]: Low-level reaction events that work with uncached messages
*[Payload]: Data structure containing information about Discord events
*[PartialEmoji]: Emoji representation for Unicode or custom emojis
*[Guild ID]: Unique identifier for a Discord server
*[Role ID]: Unique identifier for a Discord role
*[HTTPException]: Exception raised when Discord API requests fail
*[Voice Channel]: Audio communication channel in Discord
*[Event Loop]: Core asyncio component that manages async operations
*[Stream]: Playing audio directly from URL without downloading
*[AutoMod]: Discord's automated moderation system for filtering content
*[Trigger]: A condition that activates an AutoMod rule when met
*[Action]: The response taken when an AutoMod rule is triggered
*[Preset]: Pre-configured AutoMod keyword lists for common content types
*[Transformer]: A class that converts user input to specific types for app commands
*[Range]: A transformer that limits numeric or string parameter values
*[Rename]: A decorator that changes parameter display names in Discord
*[Describe]: A decorator that adds descriptions to command parameters
*[Locale]: A language/region setting for internationalization
*[Translation]: Converting command names and descriptions to different languages
*[Translator]: A class that handles command localization
*[Install]: Configuration for where an app command can be used (guild/user)
*[Context Menu]: Right-click commands available on users or messages
*[Command Group]: A collection of related slash commands under a parent name
*[Subcommand]: A command nested under a command group
*[Choice]: Predefined options for a command parameter
*[Autocomplete]: Dynamic suggestions shown while typing command parameters
*[Cooldown]: A time restriction preventing command spam
*[Check]: A function that validates if a user can execute a command
*[Error Handler]: A function that processes command errors and exceptions
*[Sync]: Uploading application commands to Discord's servers
*[Tree]: The structure that holds all application command state
*[Namespace]: An object containing command parameter values
*[Payload]: Raw data received from Discord's API
*[Raw Event]: Low-level Discord events that bypass the cache
*[Cache]: Stored Discord objects for faster access
*[State]: The internal connection state managing cached objects
*[Shard]: A connection partition for large bots across multiple processes
*[Gateway]: Discord's WebSocket connection for real-time communication
*[Heartbeat]: Regular ping to maintain WebSocket connection
*[Resume]: Reconnecting to Discord after a connection interruption
*[Identify]: Initial authentication when connecting to Discord
*[Presence]: A user's online status and activity information
*[Activity]: What a user is currently doing (playing, listening, etc.)
*[Status]: Online state (online, idle, dnd, offline)
*[Voice State]: Information about a user's voice channel connection
*[Stage Instance]: A live audio event in a stage channel
*[Scheduled Event]: A planned event in a Discord server
*[Onboarding]: Discord's server setup flow for new members
*[Welcome Screen]: Customizable greeting for new server members
*[Template]: A blueprint for creating servers with predefined settings
*[Widget]: An embeddable Discord server information display
*[Invite Target]: The destination type for an invite (stream, embedded app)
*[Vanity URL]: A custom invite link for partnered servers
*[Verification Level]: Security requirements for server participation
*[Content Filter]: Automatic scanning of explicit content
*[Notification Level]: Default notification settings for server members
*[MFA Level]: Multi-factor authentication requirement for moderation
*[NSFW Level]: Age-restriction classification for servers
*[Boost]: Premium perks purchased for a server
*[Tier]: Server boost level determining available features
*[Feature]: Special capabilities available to certain servers
*[Integration]: Connection between Discord and external services
*[Subscription]: Recurring payment for premium features
*[Entitlement]: Access rights to premium features or content
*[SKU]: Stock Keeping Unit for Discord's monetization features
*[Collectible]: Special profile decorations available for purchase
*[Soundboard]: Custom audio clips that can be played in voice channels
*[Poll]: Interactive voting system within messages
*[Forum]: A channel type for organized discussion topics
*[Tag]: Labels used to categorize forum posts
*[Reaction Type]: The kind of reaction (emoji, super reaction)
*[Voice Effect]: Visual animations triggered in voice channels
*[Audit Log]: A record of administrative actions in a server
*[Overwrite]: Permission settings for specific roles or users in channels
*[Bulk Delete]: Removing multiple messages simultaneously
*[Prune]: Removing inactive members from a server
*[Timeout]: Temporarily restricting a member's ability to participate
*[Slowmode]: Rate limiting for message sending in channels
*[Thread Archive]: Hiding inactive threads from the channel view
*[Thread Lock]: Preventing new messages in a thread
*[Mention]: Highlighting a user, role, or channel in a message
*[Reference]: A reply or quote relationship between messages
*[Attachment]: A file uploaded with a Discord message
*[Embed Field]: A structured data section within an embed
*[Embed Footer]: Bottom text section of an embed
*[Embed Author]: Top attribution section of an embed
*[Embed Thumbnail]: Small image displayed in an embed
*[Color]: Hex color value for embed styling
*[Timestamp]: Date and time information in embeds
*[Asset]: A Discord CDN resource like avatars or icons
*[Hash]: Unique identifier for Discord assets
*[Animated]: Moving images like GIFs in emojis or avatars
*[Format]: File type specification for Discord assets
*[Size]: Pixel dimensions for requesting Discord images
*[Opus]: Audio codec used for Discord voice communication
*[PCM]: Raw audio format for voice processing
*[Decoder]: Component that converts audio formats
*[Encoder]: Component that compresses audio for transmission
*[Bitrate]: Audio quality setting for voice channels
*[Sample Rate]: Audio frequency specification
*[Channels]: Audio channel count (mono, stereo)
*[Packet]: Individual data unit in voice communication
*[Jitter]: Variation in packet arrival times
*[Latency]: Delay in voice communication
*[RTP]: Real-time Transport Protocol for voice data
*[Backoff]: Exponential delay strategy for reconnection attempts
*[Rate Limit]: API request frequency restrictions
*[Bucket]: Rate limiting category for similar requests
*[Reset]: Time when rate limit counters refresh
*[Retry After]: Delay before retrying a rate-limited request
*[Global Rate Limit]: Account-wide API request restrictions
*[Route]: API endpoint path for specific operations
*[Method]: HTTP verb (GET, POST, PUT, DELETE) for API requests
*[Headers]: HTTP metadata sent with API requests
*[Query Parameters]: URL parameters for filtering API responses
*[JSON Body]: Request data sent in JSON format
*[Response Code]: HTTP status indicating request success or failure
*[Webhook Token]: Authentication for webhook operations
*[Webhook Avatar]: Custom image for webhook messages
*[Webhook Username]: Display name for webhook messages
*[Application]: Discord app containing bots and commands
*[Client ID]: Unique identifier for Discord applications
*[Client Secret]: Private key for OAuth2 authentication
*[Bot Token]: Authentication credential for bot accounts
*[OAuth2]: Authorization protocol for Discord integrations
*[Scope]: Permission level requested during OAuth2 flow
*[Redirect URI]: Callback URL for OAuth2 authentication
*[Grant Type]: OAuth2 flow method (authorization code, client credentials)
*[Access Token]: Temporary credential for API access
*[Refresh Token]: Long-term credential for renewing access tokens
*[Bearer Token]: Authorization header format for API requests
