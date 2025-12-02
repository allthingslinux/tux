---
title: Style Guide
tags:
  - style-guide
  - docs
  - css
---

# Style Guide

This guide demonstrates the standard typography, formatting, components, and code styles used throughout the Tux documentation. Use this reference to ensure consistency when writing new content.

=== "Typography"

    ## Headings

    The following headings demonstrate the typographic scale.

    # H1: Main Page Title
    ## H2: Section Title
    ### H3: Subsection Title
    #### H4: Minor Heading
    ##### H5: Small Heading
    ###### H6: Tiny Heading

    ## Paragraph Text

    **Standard Paragraph (16px)**
    How vexingly quick daft zebras jump. This is standard paragraph text that should render at exactly 16px. The quick brown fox jumps over the lazy dog. Typography is the art and technique of arranging type to make written language legible, readable and appealing when displayed.

    **Small Text**
    <small>This is small text (13.33px). Useful for captions, footnotes, and secondary information.</small>

    **Extra Small Text**
    <small class="smaller">This is extra small text (11.11px). Use this for very fine print or disclaimers.</small>

    ## Inline Styles

    - **Bold**: `**Bold**` or `__Bold__`
    - *Italic*: `*Italic*` or `_Italic_`
    - ***Bold Italic***: `***Bold Italic***`
    - ~~Strikethrough~~: `~~Strikethrough~~`
    - `Inline Code`: `` `Inline Code` ``
    - [Link](https://example.com): `[Link](https://example.com)`
    - ^^Superscript^^: `^^Superscript^^`
    - ~~Subscript~~: `~~Subscript~~` (using tilde syntax if enabled, otherwise HTML <sub>)
    - ==Highlight==: `==Highlight==`

    ## Blockquotes

    > This is a blockquote. It is used for highlighting key takeaways or citations.
    >
    > It can span multiple paragraphs.

=== "Components"

    ## Admonitions

    Admonitions are used to call attention to important information.

    !!! note
        **Note:** Useful for general information or context.

    !!! tip
        **Tip:** Helpful advice or shortcuts.

    !!! success
        **Success:** Indicates a successful action or positive outcome.

    !!! warning
        **Warning:** Alerts the user to potential issues or important caveats.

    !!! failure
        **Failure:** Indicates a failed action or negative outcome.

    !!! danger
        **Danger:** Critical warning where data loss or severe issues could occur.

    !!! bug
        **Bug:** Highlights a known issue or bug.

    !!! example
        **Example:** Provides a practical example of a concept.

    !!! quote
        **Quote:** Citations or quoted text.

    ## Collapsible Details

    ??? info "Click to expand"
        This is a collapsible details block. It's useful for hiding optional or advanced details.

        You can put any content inside, including code blocks.

    ## Content Tabs

    === "Python"
        ```python
        print("Hello from Python tab")
        ```

    === "JavaScript"
        ```javascript
        console.log("Hello from JS tab");
        ```

    ## Task Lists

    - [x] Completed task
    - [ ] Pending task
    - [ ] Another pending task

=== "Code"

    ## Code Blocks

    ### Python
    ```python title="example.py"
    def hello_world():
        """A simple function."""
        print("Hello, World!")
        return True
    ```

    ### Bash
    ```bash title="Terminal"
    # Install dependencies
    uv sync

    # Run the bot
    uv run tux start
    ```

    ### JSON
    ```json title="config.json"
    {
      "name": "Tux",
      "version": "1.0.0",
      "active": true
    }
    ```

    ## Code Annotations

    ```python
    def connect_db():
        db = Database() # (1)
        db.connect()    # (2)
        return db
    ```

    1.  Initialize the database connection object.
    2.  Establish the actual connection to the server.

=== "Colors"

    ## Color Palette Demo

    <!-- TODO: Add interactive color palette demo showcasing Tokyo Night and Catppuccin Latte themes -->
    <!-- Include primary, accent, default, and code syntax colors -->
    <!-- Add click-to-copy functionality for CSS variables -->
    <!-- Support theme switching between dark/light modes -->

    *Coming soon: Interactive color palette demonstration*

=== "Formatting"

    ## Lists

    ### Unordered
    - Item One
    - Item Two
        - Nested Item A
        - Nested Item B
    - Item Three

    ### Ordered
    1. First Step
    2. Second Step
        1. Sub-step A
        2. Sub-step B
    3. Third Step

    ## Tables

    | Feature | Status | Notes |
    | :------ | :----- | :---- |
    | Auth    | ✅ Ready | OAuth2 implemented |
    | API     | 🚧 WIP   | Rate limiting pending |
    | UI      | ❌ todo  | Needs design |

    ## Horizontal Rule

    ---
    (The line above is a horizontal rule)

=== "Diagnostics"

    ## Type Scale Diagnostic

    This interactive tool measures the actual computed font sizes of elements on this page to verify they match our design system specifications.

    ### Font Size Measurements

    <table>
        <thead>
            <tr>
                <th>Element</th>
                <th>Target Size</th>
                <th>Actual Size</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>H1 Heading</strong></td>
                <td><code>47.78px</code></td>
                <td><span class="font-size-display" data-selector="h1">---</span></td>
            </tr>
            <tr>
                <td><strong>H2 Heading</strong></td>
                <td><code>39.81px</code></td>
                <td><span class="font-size-display" data-selector="h2">---</span></td>
            </tr>
            <tr>
                <td><strong>H3 Heading</strong></td>
                <td><code>33.18px</code></td>
                <td><span class="font-size-display" data-selector="h3">---</span></td>
            </tr>
            <tr>
                <td><strong>H4 Heading</strong></td>
                <td><code>27.65px</code></td>
                <td><span class="font-size-display" data-selector="h4">---</span></td>
            </tr>
            <tr>
                <td><strong>Paragraph</strong></td>
                <td><code>16.00px</code></td>
                <td><span class="font-size-display" data-selector="p">---</span></td>
            </tr>
            <tr>
                <td><strong>Small Text</strong></td>
                <td><code>13.33px</code></td>
                <td><span class="font-size-display" data-selector="small">---</span></td>
            </tr>
        </tbody>
    </table>

    ### Environment Information

    <table>
        <thead>
            <tr>
                <th>Property</th>
                <th>Value</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Viewport</strong></td>
                <td><code class="env-value" id="viewport-info">calculating...</code></td>
            </tr>
            <tr>
                <td><strong>Root Font Size</strong></td>
                <td><code class="env-value" id="html-font-size">calculating...</code></td>
            </tr>
            <tr>
                <td><strong>Base REM Unit</strong></td>
                <td><code class="env-value" id="base-rem">calculating...</code></td>
            </tr>
        </tbody>
    </table>

    <style>
    /* Typography Diagnostic Table Styles */
    .md-typeset table {
        margin: 1.5rem 0 !important;
        border-collapse: collapse !important;
        width: 100% !important;
        border-radius: 0.5rem !important;
        overflow: hidden !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
    }

    .md-typeset table thead th {
        background: var(--md-primary-fg-color) !important;
        color: var(--md-primary-bg-color) !important;
        font-weight: 600 !important;
        padding: 1rem !important;
        text-align: left !important;
        border: none !important;
    }

    .md-typeset table tbody td {
        padding: 1rem !important;
        border-bottom: 1px solid var(--md-border-color) !important;
        vertical-align: middle !important;
    }

    .md-typeset table tbody tr:nth-child(even) {
        background: var(--md-default-bg-color--light) !important;
    }

    .md-typeset table tbody tr:hover {
        background: var(--md-accent-fg-color--transparent) !important;
    }

    /* Dark mode table styling */
    [data-md-color-scheme="tokyo-night"] .md-typeset table {
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
    }

    [data-md-color-scheme="tokyo-night"] .md-typeset table tbody tr:nth-child(even) {
        background: rgba(26, 27, 38, 0.3) !important;
    }

    [data-md-color-scheme="tokyo-night"] .md-typeset table tbody tr:hover {
        background: rgba(122, 162, 247, 0.1) !important;
    }

    /* Font size display styling */
    .font-size-display {
        font-family: var(--md-code-font) !important;
        font-weight: 600 !important;
        color: var(--md-primary-fg-color) !important;
        background: var(--md-code-bg-color) !important;
        padding: 0.25rem 0.5rem !important;
        border-radius: 0.25rem !important;
        display: inline-block !important;
        min-width: 60px !important;
        text-align: center !important;
    }

    /* Environment value styling */
    .env-value {
        font-family: var(--md-code-font) !important;
        font-size: 0.875rem !important;
        padding: 0.5rem !important;
        background: var(--md-default-bg-color) !important;
        border-radius: 0.25rem !important;
        display: inline-block !important;
        font-weight: 600 !important;
        color: var(--md-primary-fg-color) !important;
        border: 1px solid var(--md-border-color) !important;
    }


    /* Responsive table styling */
    @media screen and (max-width: 76.25em) {
        .md-typeset table {
            font-size: 0.875rem !important;
        }

        .md-typeset table thead th,
        .md-typeset table tbody td {
            padding: 0.75rem 0.5rem !important;
        }
    }

    @media screen and (max-width: 48em) {
        .md-typeset table {
            font-size: 0.8rem !important;
        }

        .md-typeset table thead th,
        .md-typeset table tbody td {
            padding: 0.5rem 0.25rem !important;
        }
    }
    </style>
