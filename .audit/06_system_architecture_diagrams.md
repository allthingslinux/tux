# System Architecture Diagrams

## 1. Overall System Architecture

```mermaid
graph TB
    subgraph "Entry Point"
        A[main.py] --> B[TuxApp]
    end
    
    subgraph "Application Core"
        B --> C[Tux Bot Instance]
        C --> D[Setup Process]
        D --> E[Database Connection]
        D --> F[CogLoader]
        D --> G[Error Handlers]
        D --> H[Monitoring Setup]
    end
    
    subgraph "Cog Loading System"
        F --> I[Handlers Loading]
        F --> J[Cogs Loading]
        F --> K[Extensions Loading]
        
        I --> L[Error Handler]
        I --> M[Event Handler]
        I --> N[Activity Handler]
        I --> O[Sentry Handler]
    end
    
    subgraph "Cog Categories"
        J --> P[Admin Cogs]
        J --> Q[Moderation Cogs]
        J --> R[Service Cogs]
        J --> S[Utility Cogs]
        J --> T[Info Cogs]
        J --> U[Fun Cogs]
        J --> V[Guild Cogs]
        J --> W[Levels Cogs]
        J --> X[Snippets Cogs]
        J --> Y[Tools Cogs]
    end
    
    subgraph "Core Services"
        P --> Z[DatabaseController]
        Q --> Z
        R --> Z
        S --> Z
        T --> Z
        U --> Z
        V --> Z
        W --> Z
        X --> Z
        Y --> Z
        
        Z --> AA[BaseController]
        AA --> BB[Prisma Client]
        BB --> CC[(PostgreSQL Database)]
    end
    
    subgraph "External Integrations"
        C --> DD[Discord API]
        H --> EE[Sentry Service]
        L --> EE
    end
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#fff3e0
    style Z fill:#e8f5e8
    style CC fill:#ffebee
```

## 2. Cog Initialization Pattern

```mermaid
sequenceDiagram
    participant CL as CogLoader
    participant C as Cog Class
    participant B as Bot Instance
    participant DC as DatabaseController
    participant BC as BaseController
    participant PC as PrismaClient
    
    CL->>C: Instantiate cog
    C->>B: Store bot reference
    C->>DC: Create new instance
    DC->>BC: Initialize controllers
    BC->>PC: Connect to database
    C->>C: Generate command usage
    C-->>CL: Cog ready
    
    Note over C,DC: This pattern repeats<br/>for every cog (40+ times)
```

## 3. Database Access Architecture

```mermaid
graph TB
    subgraph "Cog Layer"
        A[Admin Cogs] --> E[DatabaseController]
        B[Moderation Cogs] --> E
        C[Service Cogs] --> E
        D[Other Cogs] --> E
    end
    
    subgraph "Controller Layer"
        E --> F[AfkController]
        E --> G[CaseController]
        E --> H[GuildController]
        E --> I[GuildConfigController]
        E --> J[LevelsController]
        E --> K[NoteController]
        E --> L[ReminderController]
        E --> M[SnippetController]
        E --> N[StarboardController]
        E --> O[StarboardMessageController]
    end
    
    subgraph "Base Layer"
        F --> P[BaseController]
        G --> P
        H --> P
        I --> P
        J --> P
        K --> P
        L --> P
        M --> P
        N --> P
        O --> P
    end
    
    subgraph "ORM Layer"
        P --> Q[Prisma Client]
        Q --> R[(Database)]
    end
    
    subgraph "Operations"
        P --> S[CRUD Operations]
        P --> T[Transaction Management]
        P --> U[Error Handling]
        P --> V[Query Building]
    end
    
    style E fill:#ffecb3
    style P fill:#c8e6c9
    style Q fill:#f8bbd9
    style R fill:#ffcdd2
```

## 4. Error Handling Flow

```mermaid
flowchart TD
    A[Command Executed] --> B{Error Occurs?}
    B -->|No| C[Normal Response]
    B -->|Yes| D[Error Caught]
    
    D --> E[ErrorHandler.handle_error]
    E --> F[Unwrap Nested Errors]
    F --> G[Look up Error Config]
    
    G --> H{Config Found?}
    H -->|Yes| I[Use Config Settings]
    H -->|No| J[Use Default Handling]
    
    I --> K[Extract Error Details]
    J --> K
    K --> L[Format User Message]
    L --> M[Create Error Embed]
    M --> N[Send to User]
    
    N --> O[Log Error]
    O --> P{Send to Sentry?}
    P -->|Yes| Q[Report to Sentry]
    P -->|No| R[Skip Sentry]
    
    Q --> S[Add Event ID to Message]
    R --> T[Complete]
    S --> T
    
    style D fill:#ffcdd2
    style E fill:#fff3e0
    style Q fill:#e1f5fe
```

## 5. Command Execution Lifecycle

```mermaid
sequenceDiagram
    participant U as User
    participant D as Discord
    participant B as Bot
    participant C as Cog
    participant DB as Database
    participant EH as ErrorHandler
    participant S as Sentry
    
    U->>D: Send command
    D->>B: Command event
    B->>C: Route to cog
    
    alt Success Path
        C->>DB: Database operation
        DB-->>C: Return data
        C->>D: Send response
        D-->>U: Show response
    else Error Path
        C->>EH: Exception thrown
        EH->>S: Report error
        EH->>D: Send error message
        D-->>U: Show error
    end
    
    Note over B,S: Sentry tracks performance<br/>and error metrics
```

## 6. Moderation System Architecture

```mermaid
graph TB
    subgraph "Moderation Commands"
        A[Ban] --> E[ModerationCogBase]
        B[Kick] --> E
        C[Timeout] --> E
        D[Warn] --> E
    end
    
    subgraph "Base Functionality"
        E --> F[Permission Checks]
        E --> G[User Validation]
        E --> H[Action Execution]
        E --> I[Case Creation]
        E --> J[DM Handling]
        E --> K[Logging]
    end
    
    subgraph "Database Operations"
        I --> L[CaseController]
        L --> M[BaseController]
        M --> N[Prisma Client]
    end
    
    subgraph "External Actions"
        H --> O[Discord API]
        J --> P[Direct Messages]
        K --> Q[Log Channels]
    end
    
    subgraph "Error Handling"
        F --> R[ErrorHandler]
        G --> R
        H --> R
        I --> R
    end
    
    style E fill:#fff3e0
    style L fill:#e8f5e8
    style R fill:#ffcdd2
```

## 7. Service Layer Architecture (Current State)

```mermaid
graph LR
    subgraph "Presentation Layer (Cogs)"
        A[Command Handlers]
        B[Event Listeners]
        C[Slash Commands]
    end
    
    subgraph "Mixed Layer (Current Issue)"
        D[Business Logic in Cogs]
        E[Database Calls in Cogs]
        F[Discord API Calls in Cogs]
    end
    
    subgraph "Data Layer"
        G[DatabaseController]
        H[BaseController]
        I[Prisma Client]
    end
    
    A --> D
    B --> D
    C --> D
    D --> E
    D --> F
    E --> G
    G --> H
    H --> I
    
    style D fill:#ffcdd2
    style E fill:#ffcdd2
    style F fill:#ffcdd2
    
    classDef problem fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px
    classDef good fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    
    class D,E,F problem
    class G,H,I good
```

## 8. Dependency Relationships

```mermaid
graph TD
    subgraph "Core Dependencies"
        A[TuxApp] --> B[Tux Bot]
        B --> C[CogLoader]
        B --> D[ErrorHandler]
        B --> E[Database Client]
    end
    
    subgraph "Cog Dependencies"
        C --> F[Individual Cogs]
        F --> G[DatabaseController]
        F --> H[EmbedCreator]
        F --> I[Utils Functions]
        F --> J[Config]
    end
    
    subgraph "Circular Dependencies (Issues)"
        K[Moderation Base] -.-> L[Moderation Cogs]
        L -.-> K
        M[Utils] -.-> N[Cogs]
        N -.-> M
    end
    
    subgraph "External Dependencies"
        B --> O[Discord.py]
        D --> P[Sentry SDK]
        E --> Q[Prisma]
        G --> Q
    end
    
    style K fill:#ffcdd2
    style L fill:#ffcdd2
    style M fill:#ffcdd2
    style N fill:#ffcdd2
```

## 9. Configuration Management

```mermaid
graph TB
    subgraph "Configuration Sources"
        A[Environment Variables] --> D[Config Class]
        B[YAML Settings] --> D
        C[Database Settings] --> D
    end
    
    subgraph "Configuration Access"
        D --> E[Direct Import in Cogs]
        D --> F[Bot Instance Access]
        D --> G[Utils Functions]
    end
    
    subgraph "Configuration Usage"
        E --> H[Command Behavior]
        E --> I[Feature Flags]
        E --> J[API Keys]
        E --> K[Database Settings]
    end
    
    subgraph "Issues"
        L[Scattered Access]
        M[No Centralized Management]
        N[Hard to Test]
    end
    
    E -.-> L
    F -.-> L
    G -.-> L
    
    style L fill:#ffcdd2
    style M fill:#ffcdd2
    style N fill:#ffcdd2
```

## 10. Testing Architecture (Current Limitations)

```mermaid
graph TB
    subgraph "Current Testing Challenges"
        A[Tight Coupling] --> D[Hard to Mock]
        B[Direct DB Access] --> D
        C[Mixed Concerns] --> D
    end
    
    subgraph "Testing Layers"
        E[Unit Tests] --> F[Limited Coverage]
        G[Integration Tests] --> H[Complex Setup]
        I[End-to-End Tests] --> J[Brittle Tests]
    end
    
    subgraph "Desired Testing Architecture"
        K[Dependency Injection] --> L[Easy Mocking]
        M[Service Layer] --> N[Isolated Testing]
        O[Clear Interfaces] --> P[Contract Testing]
    end
    
    style A fill:#ffcdd2
    style B fill:#ffcdd2
    style C fill:#ffcdd2
    style F fill:#ffcdd2
    style H fill:#ffcdd2
    style J fill:#ffcdd2
    
    style K fill:#c8e6c9
    style L fill:#c8e6c9
    style M fill:#c8e6c9
    style N fill:#c8e6c9
    style O fill:#c8e6c9
    style P fill:#c8e6c9
```

These diagrams illustrate the current architecture and highlight both the strengths and areas for improvement in the Tux Discord bot system. The visual representation makes it clear where architectural debt exists and provides a foundation for the improvement recommendations.
