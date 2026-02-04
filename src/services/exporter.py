"""HTML export for email-friendly recipe sharing."""

import re
import markdown


def parse_duration_to_ms(duration_str: str) -> int:
    """Parse duration string to milliseconds.

    Supports formats like: 15m, 1h30m, 45s, 1h
    """
    hours = re.search(r"(\d+)h", duration_str)
    minutes = re.search(r"(\d+)m", duration_str)
    seconds = re.search(r"(\d+)s", duration_str)

    total_seconds = 0
    if hours:
        total_seconds += int(hours.group(1)) * 3600
    if minutes:
        total_seconds += int(minutes.group(1)) * 60
    if seconds:
        total_seconds += int(seconds.group(1))

    return total_seconds * 1000 if total_seconds > 0 else 0


def extract_context_label(text: str, match_start: int, max_length: int = 50) -> str:
    """Extract context around a timer match to create a meaningful label.

    Args:
        text: Full text content
        match_start: Position where timer match starts
        max_length: Maximum length of label

    Returns:
        Extracted context string suitable for timer label
    """
    # Find start of sentence or line
    line_start = text.rfind("\n", 0, match_start)
    if line_start == -1:
        line_start = 0
    else:
        line_start += 1

    # Extract text from line start to match
    context = text[line_start:match_start].strip()

    # Remove list markers
    context = re.sub(r"^\d+\.\s*", "", context)
    context = re.sub(r"^[-*]\s*", "", context)

    # Truncate if too long
    if len(context) > max_length:
        context = context[:max_length].rsplit(" ", 1)[0] + "..."

    return context if context else "Timer"


def inject_timer_buttons(content: str) -> tuple[str, list[dict]]:
    """Inject timer buttons into recipe content.

    Detects both explicit timer syntax and natural language time references.

    Returns:
        - Modified content with timer button placeholders
        - List of detected timers with metadata
    """
    timers = []
    timer_id = 0
    modified_content = content

    # Step 1: Process explicit syntax [timer:15m:Label] or [timer:15m] or [15m]
    explicit_pattern = r"\[(?:timer:)?([0-9hms]+)(?::([^\]]+))?\]"

    def replace_explicit(match):
        nonlocal timer_id
        duration_str = match.group(1)
        custom_label = match.group(2)

        # Parse duration
        duration_ms = parse_duration_to_ms(duration_str)
        if duration_ms == 0:
            return match.group(0)  # Invalid duration, leave as-is

        # Determine label
        if custom_label:
            label = custom_label.strip()
        else:
            label = extract_context_label(modified_content, match.start())

        timer_info = {
            "id": timer_id,
            "duration": duration_str,
            "duration_ms": duration_ms,
            "label": label,
        }
        timers.append(timer_info)

        # Replace with button placeholder
        button_html = f'<button class="timer-btn" data-timer-id="{timer_id}" data-duration="{duration_str}" data-label="{label}">⏱ {duration_str}</button>'
        timer_id += 1

        return button_html

    modified_content = re.sub(explicit_pattern, replace_explicit, modified_content)

    # Step 2: Auto-detect time patterns in natural language
    # Pattern: "for X minutes/hours/seconds" or "about X minutes"
    auto_pattern = r"\b(?:for|about)\s+(\d+)(?:-(\d+))?\s*(minutes?|mins?|hours?|hrs?|seconds?|secs?)\b"

    matches = list(re.finditer(auto_pattern, modified_content, re.IGNORECASE))

    # Process matches in reverse to maintain string positions
    for match in reversed(matches):
        min_value = int(match.group(1))
        max_value = int(match.group(2)) if match.group(2) else min_value
        unit = match.group(3).lower()

        # Use maximum value for ranges
        value = max_value

        # Normalize unit to short form
        if unit.startswith("hour") or unit.startswith("hr"):
            duration_str = f"{value}h"
        elif unit.startswith("min"):
            duration_str = f"{value}m"
        elif unit.startswith("sec"):
            duration_str = f"{value}s"
        else:
            continue

        duration_ms = parse_duration_to_ms(duration_str)
        label = extract_context_label(modified_content, match.start())

        timer_info = {
            "id": timer_id,
            "duration": duration_str,
            "duration_ms": duration_ms,
            "label": label,
        }
        timers.append(timer_info)

        # Insert button after the matched text
        button_html = f' <button class="timer-btn" data-timer-id="{timer_id}" data-duration="{duration_str}" data-label="{label}">⏱ {duration_str}</button>'
        modified_content = (
            modified_content[: match.end()] + button_html + modified_content[match.end() :]
        )
        timer_id += 1

    return modified_content, timers


def recipe_to_html(raw_content: str) -> str:
    """Convert markdown recipe to styled HTML for email.

    Returns HTML that pastes cleanly into Gmail and other email clients.
    """
    # Strip YAML frontmatter if present
    content = raw_content
    if content.startswith("---"):
        end_marker = content.find("---", 3)
        if end_marker != -1:
            content = content[end_marker + 3 :].lstrip()

    # Inject timer buttons before markdown conversion
    content_with_timers, _ = inject_timer_buttons(content)

    # Convert markdown to HTML
    html = markdown.markdown(
        content_with_timers,
        extensions=["tables", "fenced_code"],
    )

    # Wrap in minimal styling for email clients
    styled_html = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 600px;">
{html}
</div>
""".strip()

    return styled_html


def shopping_list_to_text(
    shopping_items: list[dict],
    pantry_items: list[str],
) -> str:
    """Format shopping list for copy/paste.

    Args:
        shopping_items: List of dicts with 'display' key
        pantry_items: List of pantry item names to include

    Returns:
        Plain text with one item per line, no headers
    """
    lines = []

    # Add shopping items (one per line, no category headers)
    for item in shopping_items:
        lines.append(item.get("display", item.get("name", "")))

    # Add pantry items if any selected
    for item in sorted(pantry_items):
        lines.append(item)

    return "\n".join(lines)
