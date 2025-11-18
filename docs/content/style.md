<!-- markdownlint-disable -->

# Typography Style Guide

This page demonstrates all typography styles and the type scale system.

## Headings

### H1 - Target: 47.78px | Actual: <span class="font-size-display" data-selector="h1" data-index="0">measuring...</span>

# How vexingly quick daft zebras jump

### H2 - Target: 39.81px | Actual: <span class="font-size-display" data-selector="h2" data-index="0">measuring...</span>

## How vexingly quick daft zebras jump

### H3 - Target: 33.18px | Actual: <span class="font-size-display" data-selector="h3" data-index="0">measuring...</span>

### How vexingly quick daft zebras jump

### H4 - Target: 27.65px | Actual: <span class="font-size-display" data-selector="h4" data-index="0">measuring...</span>

#### How vexingly quick daft zebras jump

### H5 - Target: 23.04px | Actual: <span class="font-size-display" data-selector="h5" data-index="0">measuring...</span>

##### How vexingly quick daft zebras jump

### H6 - Target: 19.2px | Actual: <span class="font-size-display" data-selector="h6" data-index="0">measuring...</span>

###### How vexingly quick daft zebras jump

## Paragraph Text

### Standard Paragraph - Target: 16px | Actual: <span class="font-size-display" data-selector="p" data-index="0">measuring...</span>

How vexingly quick daft zebras jump. This is standard paragraph text that should render at exactly 16px. The quick brown fox jumps over the lazy dog. Typography is the art and technique of arranging type to make written language legible, readable and appealing when displayed.

### Multiple Paragraphs

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

## Small Text - Target: 13.33px | Actual: <span class="font-size-display" data-selector="small" data-index="0">measuring...</span>

<small>How vexingly quick daft zebras jump. This is small text that should render at 13.33px. Small text is useful for captions, footnotes, and secondary information.</small>

## Extra Small Text - Target: 11.11px | Actual: <span class="font-size-display" data-selector=".smaller" data-index="0">measuring...</span>

<small class="smaller">How vexingly quick daft zebras jump. This is extra small text that should render at 11.11px. Use this for very fine print or disclaimers.</small>

## Lists

### Unordered List

- First item in an unordered list
- Second item with some longer text that wraps to multiple lines to test line height and spacing
- Third item
  - Nested item one
  - Nested item two
- Fourth item

### Ordered List

1. First item in an ordered list
2. Second item with some longer text that wraps to multiple lines to test line height and spacing
3. Third item
   1. Nested item one
   2. Nested item two
4. Fourth item

## Inline Elements

This paragraph contains **bold text**, *italic text*, `inline code`, and a [link](https://example.com) to demonstrate inline typography.

## Code Blocks

```python
def hello_world():
    """A simple function to demonstrate code typography."""
    print("Hello, World!")
    return True
```

## Blockquotes

> This is a blockquote. It should maintain proper typography and spacing.
>
> Blockquotes can span multiple paragraphs and are useful for highlighting important information or citations.

## Horizontal Rules

---

## Mixed Content

### Heading with Paragraph

This is a paragraph that follows an H3 heading. It demonstrates the spacing and relationship between headings and body text.

### Lists with Paragraphs

Here's a paragraph before a list:

- List item one
- List item two
- List item three

And here's a paragraph after a list to show spacing.

## Type Scale Summary

| Element | Target Size | Rendered Size |
|---------|-------------|---------------|
| H1 | 47.78px | <span class="font-size-display" data-selector="h1">measuring...</span> |
| H2 | 39.81px | <span class="font-size-display" data-selector="h2">measuring...</span> |
| H3 | 33.18px | <span class="font-size-display" data-selector="h3">measuring...</span> |
| H4 | 27.65px | <span class="font-size-display" data-selector="h4">measuring...</span> |
| H5 | 23.04px | <span class="font-size-display" data-selector="h5">measuring...</span> |
| H6 | 19.2px | <span class="font-size-display" data-selector="h6">measuring...</span> |
| Paragraph (p) | 16px | <span class="font-size-display" data-selector="p">measuring...</span> |
| Small | 13.33px | <span class="font-size-display" data-selector="small">measuring...</span> |
| Smaller | 11.11px | <span class="font-size-display" data-selector=".smaller">measuring...</span> |

## Responsive Testing

This page should render correctly at all screen sizes:

- **Small screens** (< 100em): html font-size 125% (1rem = 20px)
- **Medium screens** (≥ 100em): html font-size 137.5% (1rem = 22px)
- **Large screens** (≥ 125em): html font-size 150% (1rem = 24px)

Paragraphs should always render at exactly 16px regardless of screen size.

---

## Debug Information

<div id="typography-debug" style="margin-top: 2rem; padding: 1rem; background: var(--md-code-bg-color); border-radius: 0.2rem; font-family: var(--md-code-font); font-size: 0.875rem;">
  <strong>Current Viewport:</strong> <span id="viewport-info">calculating...</span><br>
  <strong>HTML Font-Size:</strong> <span id="html-font-size">calculating...</span><br>
  <strong>Base Rem:</strong> <span id="base-rem">calculating...</span>
</div>

<script>
(function() {
  'use strict';
  
  // Function to get computed font-size in pixels
  function getFontSize(element) {
    if (!element) return null;
    const computed = window.getComputedStyle(element);
    return parseFloat(computed.fontSize);
  }
  
  // Function to update all font-size displays
  function updateFontSizes() {
    // Update viewport info
    const viewportInfo = document.getElementById('viewport-info');
    const htmlFontSize = document.getElementById('html-font-size');
    const baseRem = document.getElementById('base-rem');

    if (viewportInfo) {
      const width = window.innerWidth;
      const widthEm = width / parseFloat(getComputedStyle(document.documentElement).fontSize);
      viewportInfo.textContent = `${width}px (${widthEm.toFixed(2)}em)`;
    }

    if (htmlFontSize) {
      const htmlSize = parseFloat(getComputedStyle(document.documentElement).fontSize);
      htmlFontSize.textContent = `${htmlSize.toFixed(2)}px (${(htmlSize / 16 * 100).toFixed(1)}%)`;
    }

    if (baseRem) {
      const base = parseFloat(getComputedStyle(document.documentElement).fontSize);
      baseRem.textContent = `1rem = ${base.toFixed(2)}px`;
    }

    // Update all font-size displays
    const displays = document.querySelectorAll('.font-size-display');
    displays.forEach(display => {
      const selector = display.getAttribute('data-selector');
      const index = parseInt(display.getAttribute('data-index') || '0');

      let element = null;

      if (selector.startsWith('.')) {
        // Class selector
        const elements = document.querySelectorAll(selector);
        element = elements[index] || elements[0];
      } else {
        // Tag selector
        const elements = document.querySelectorAll(selector);
        // For headings, find the one in the same section
        if (['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(selector)) {
          // Find the heading closest to this display element
          let parent = display.parentElement;
          while (parent && parent !== document.body) {
            const heading = parent.querySelector(selector);
            if (heading) {
              element = heading;
              break;
            }
            parent = parent.parentElement;
          }
          if (!element) {
            element = document.querySelectorAll[selector](index) || document.querySelector(selector);
          }
        } else {
          // For other elements, find the one in the same section
          let parent = display.parentElement;
          while (parent && parent !== document.body) {
            const found = parent.querySelector(selector);
            if (found) {
              element = found;
              break;
            }
            parent = parent.parentElement;
          }
          if (!element) {
            element = document.querySelectorAll[selector](index) || document.querySelector(selector);
          }
        }
      }

      if (element) {
        const size = getFontSize(element);
        if (size !== null) {
          display.textContent = `${size.toFixed(2)}px`;
          display.style.color = 'var(--md-code-hl-number-color)';
          display.style.fontWeight = '600';
        } else {
          display.textContent = 'N/A';
        }
      } else {
        display.textContent = 'not found';
      }
    });
  }
  
  // Update on load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', updateFontSizes);
  } else {
    updateFontSizes();
  }
  
  // Update on resize (with debounce)
  let resizeTimeout;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(updateFontSizes, 100);
  });
  
  // Update periodically to catch any dynamic changes
  setInterval(updateFontSizes, 1000);
})();
</script>
