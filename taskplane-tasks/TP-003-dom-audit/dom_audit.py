#!/usr/bin/env python3
"""
DOM Audit Script for 2Park Dashboard
=====================================
Logs into mijn.2park.nl, navigates to the dashboard "Lopend" tab,
and dumps the full DOM structure of booking cards for selector reference.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Load credentials
load_dotenv("/home/mark/Projects/2park/.env")
EMAIL = os.environ.get("TWOPARK_EMAIL", "")
PASSWORD = os.environ.get("TWOPARK_PASSWORD", "")

if not EMAIL or not PASSWORD:
    print("ERROR: TWOPARK_EMAIL or TWOPARK_PASSWORD not found in .env")
    sys.exit(1)

TASK_DIR = Path("/home/mark/Projects/2park/.worktrees/mark-20260512T235032/lane-1/taskplane-tasks/TP-003-dom-audit")
REFERENCE_FILE = TASK_DIR / "DOM_REFERENCE.md"
SCREENSHOT_PATH = "/tmp/dashboard_dom_audit.png"


def get_tag_name(element):
    """Get tag name via evaluate since tag_name property isn't available."""
    try:
        return element.evaluate("el => el.tagName").lower()
    except Exception:
        return "unknown"


def dump_element_tree(element, max_depth=6, current_depth=0, indent=""):
    """Recursively dump element tree with tags, classes, IDs, and text."""
    lines = []
    try:
        tag = get_tag_name(element)
        cls = element.get_attribute("class") or ""
        attr_id = element.get_attribute("id") or ""
        text = (element.inner_text() or "").strip()

        parts = []
        parts.append(tag)
        if attr_id:
            parts.append(f"#{attr_id}")
        if cls:
            parts.append(f".{'.'.join(cls.split())}")

        label = " > ".join(parts)
        if text and len(text) < 100:
            label += f" | {text}"

        lines.append(f"{indent}├── {label}")

        if current_depth < max_depth:
            children = element.query_selector_all("> *")
            for child in children:
                lines.extend(dump_element_tree(child, max_depth, current_depth + 1, indent + "│   "))
    except Exception as e:
        lines.append(f"{indent}├── [error: {e}]")

    return lines


def extract_button_info(page):
    """Extract all button text and class names from the page."""
    buttons = page.query_selector_all("button, [role='button'], input[type='button'], input[type='submit']")
    results = []
    for btn in buttons:
        try:
            tag = get_tag_name(btn)
            text = (btn.inner_text() or "").strip()
            cls = btn.get_attribute("class") or ""
            attr_id = btn.get_attribute("id") or ""
            title = btn.get_attribute("title") or ""
            aria_label = btn.get_attribute("aria-label") or ""
            type_attr = btn.get_attribute("type") or ""
            name_attr = btn.get_attribute("name") or ""

            info = {
                "tag": tag,
                "text": text,
                "class": cls,
                "id": attr_id,
                "title": title,
                "aria-label": aria_label,
                "type": type_attr,
                "name": name_attr,
            }
            results.append(info)
        except Exception:
            pass
    return results


def main():
    print("Starting DOM audit...")
    findings = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        # === LOGIN ===
        print("Step 1: Logging in...")
        findings.append("## Login Flow\n")
        try:
            page.goto("https://mijn.2park.nl/login", wait_until="networkidle", timeout=30000)
            print(f"  Login page URL: {page.url}")

            # Find email/password selectors (same logic as scraper.py)
            email_selectors = [
                "#login_email", "#email", "input[name='email']", "input[name='Email']",
                "input[type='email']", ".form-email",
            ]
            password_selectors = [
                "#login_password", "#password", "input[name='password']", "input[name='Password']",
                "input[type='password']", ".form-password",
            ]

            email_selector = None
            for sel in email_selectors:
                if page.query_selector(sel):
                    email_selector = sel
                    break

            password_selector = None
            for sel in password_selectors:
                if page.query_selector(sel):
                    password_selector = sel
                    break

            if not email_selector or not password_selector:
                print(f"  ERROR: Could not find login form. email_sel={email_selector}, pw_sel={password_selector}")
                page.screenshot(path="/tmp/dom_audit_login_error.png")
                browser.close()
                sys.exit(1)

            print(f"  Found email selector: {email_selector}")
            print(f"  Found password selector: {password_selector}")
            findings.append(f"- **Email field selector:** `{email_selector}`\n")
            findings.append(f"- **Password field selector:** `{password_selector}`\n")

            page.fill(email_selector, EMAIL)
            page.fill(password_selector, PASSWORD)

            # Find submit button
            submit_selectors = [
                'button[type="submit"]', 'input[type="submit"]',
                '.btn-login', '.login-button', 'button.login',
            ]
            submit_btn = None
            submit_sel_used = None
            for sel in submit_selectors:
                btn = page.query_selector(sel)
                if btn:
                    submit_btn = btn
                    submit_sel_used = sel
                    break

            if not submit_btn:
                print("  ERROR: Could not find submit button")
                page.screenshot(path="/tmp/dom_audit_submit_error.png")
                browser.close()
                sys.exit(1)

            print(f"  Found submit button: {submit_sel_used}")
            findings.append(f"- **Submit button selector:** `{submit_sel_used}`\n")

            submit_btn.click()
            page.wait_for_load_state("networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            current_url = page.url
            print(f"  After login URL: {current_url}")

            if "login" in current_url.lower():
                print("  ERROR: Still on login page — login failed")
                page.screenshot(path="/tmp/dom_audit_login_failed.png")
                browser.close()
                sys.exit(1)

            print("  Login successful!")
            findings.append(f"- **Post-login URL:** `{current_url}`\n")

        except Exception as e:
            print(f"  Login error: {e}")
            try:
                page.screenshot(path="/tmp/dom_audit_login_exception.png")
            except Exception:
                pass
            browser.close()
            sys.exit(1)

        # === NAVIGATE TO DASHBOARD ===
        print("\nStep 2: Navigating to dashboard...")
        findings.append("\n## Dashboard Navigation\n")

        # Wait for page to stabilize
        page.wait_for_timeout(3000)
        print(f"  Dashboard URL: {page.url}")
        findings.append(f"- **Dashboard URL:** `{page.url}`\n")

        # === CLICK "LOPEND" TAB ===
        print("\nStep 3: Clicking 'Lopend' tab...")
        findings.append("\n## Tab Navigation\n")

        # Try to find and click the "Lopend" tab
        lopend_found = False

        # Strategy 1: Look for tab elements containing "Lopend"
        tab_candidates = page.query_selector_all("button, [role='tab'], a, [class*='tab']")
        for tab in tab_candidates:
            try:
                text = (tab.inner_text() or "").strip()
                if "Lopend" in text and lopend_found is False:
                    print(f"  Found 'Lopend' tab: '{text}'")
                    cls = tab.get_attribute("class") or ""
                    tag = get_tag_name(tab)
                    print(f"    Tab tag: {tag}, class: {cls}")
                    findings.append(f"- **'Lopend' tab tag:** `{tag}`\n")
                    findings.append(f"- **'Lopend' tab text:** `{text}`\n")
                    findings.append(f"- **'Lopend' tab class:** `{cls}`\n")
                    tab.click()
                    page.wait_for_timeout(2000)
                    lopend_found = True
                    break
            except Exception:
                continue

        print(f"  'Lopend' tab clicked: {lopend_found}")

        # === CAPTURE SCREENSHOT ===
        print("\nStep 4: Capturing screenshot...")
        page.screenshot(path=SCREENSHOT_PATH, full_page=False)
        print(f"  Screenshot saved to {SCREENSHOT_PATH}")

        # Also capture full page screenshot
        page.screenshot(path="/tmp/dashboard_full_dom_audit.png", full_page=True)
        print(f"  Full page screenshot saved to /tmp/dashboard_full_dom_audit.png")

        # === EXTRACT BOOKING CARD STRUCTURE ===
        print("\nStep 5: Extracting booking card structure...")
        findings.append("\n## Booking Card Structure\n")

        # Dump the full page body structure
        body = page.query_selector("body")
        if body:
            body_classes = body.get_attribute("class") or ""
            print(f"  Body classes: {body_classes}")
            findings.append(f"- **Body classes:** `{body_classes}`\n")

        # Find which selectors actually match on the dashboard
        card_selectors = [
            ".parkapp-item",
            ".booking-item",
            ".parking-item",
            "[class*='parkapp']",
            "[class*='booking']",
            "[class*='parking']",
            ".card",
            ".booking-card",
            ".parking-card",
            "article",
            ".parkapp-booking",
            "[class*='card']",
            "[class*='item']",
        ]

        # Find which selectors actually match
        matched_selectors = []
        for sel in card_selectors:
            items = page.query_selector_all(sel)
            if items:
                matched_selectors.append((sel, len(items)))
                print(f"  Selector '{sel}' matched {len(items)} elements")

        findings.append(f"\n### Selector Match Results\n")
        for sel, count in matched_selectors:
            findings.append(f"- `{sel}` → {count} matches\n")

        # Extract the main content area
        print("\n  Extracting main content area...")
        main_containers = page.query_selector_all("main, .content, .container, #root, [class*='content']")
        for mc in main_containers:
            try:
                cls = mc.get_attribute("class") or ""
                tag = get_tag_name(mc)
                findings.append(f"\n- **Main container:** `{tag}` class=`{cls}`\n")
            except Exception:
                pass

        # Dump the tab structure
        print("  Extracting tab structure...")
        findings.append("\n### Tab Container Structure\n")
        tab_containers = page.query_selector_all("[class*='tab'], [role='tablist'], .tabs, .tab-container")
        for tc in tab_containers:
            try:
                tree = dump_element_tree(tc, max_depth=4)
                findings.append(f"\n```\n")
                findings.extend(tree)
                findings.append(f"\n```\n")
                print(f"  Tab container: {' > '.join(tree[:3])}...")
            except Exception:
                pass

        # Find booking cards - try to identify the actual card containers
        print("\n  Identifying booking cards...")
        findings.append("\n### Booking Card Details\n")

        # Look for elements that contain license plates or time info
        all_cards = page.query_selector_all(
            "[class*='item'], [class*='card'], [class*='booking'], "
            "[class*='reservation'], article, .parkapp-item, .parkapp-booking"
        )

        card_count = 0
        for card in all_cards:
            if card_count >= 5:
                break
            try:
                cls = card.get_attribute("class") or ""
                tag = get_tag_name(card)
                text_preview = ((card.inner_text() or "")[:200]).replace("\n", " | ")

                findings.append(f"\n---\n")
                findings.append(f"**Card {card_count + 1}**\n")
                findings.append(f"- **Tag:** `{tag}`\n")
                findings.append(f"- **Class:** `{cls}`\n")
                findings.append(f"- **Text preview:** {text_preview}\n")

                # Dump sub-element tree
                findings.append(f"\n**Element tree:**\n")
                findings.append(f"```\n")
                tree = dump_element_tree(card, max_depth=4)
                findings.extend(tree)
                findings.append(f"```\n")

                card_count += 1
                print(f"  Card {card_count + 1}: {tag}.{cls.split()[0] if cls else ''} — {text_preview[:80]}")

            except Exception as e:
                print(f"  Card extraction error: {e}")
                continue

        # === EXTRACT ALL BUTTON INFO ===
        print("\nStep 6: Extracting all button info...")
        findings.append("\n## All Buttons on Dashboard\n")

        buttons = extract_button_info(page)
        findings.append(f"\n**Total buttons found:** {len(buttons)}\n\n")

        for i, btn in enumerate(buttons):
            findings.append(f"### Button {i+1}\n")
            findings.append(f"- **Tag:** `{btn['tag']}`\n")
            findings.append(f"- **Text:** `{btn['text']}`\n")
            findings.append(f"- **Class:** `{btn['class']}`\n")
            if btn['id']:
                findings.append(f"- **ID:** `#{btn['id']}`\n")
            if btn['title']:
                findings.append(f"- **Title:** `{btn['title']}`\n")
            if btn['aria-label']:
                findings.append(f"- **Aria-label:** `{btn['aria-label']}`\n")
            if btn['type']:
                findings.append(f"- **Type:** `{btn['type']}`\n")
            findings.append(f"\n")

        # === EXTRACT "GEPLAND" TAB ===
        print("\nStep 7: Checking 'Gepland' tab structure...")
        findings.append("\n## 'Gepland' (Scheduled) Tab\n")

        # Try to click "Gepland" tab
        gepland_found = False
        tab_candidates = page.query_selector_all("button, [role='tab'], a, [class*='tab']")
        for tab in tab_candidates:
            try:
                text = (tab.inner_text() or "").strip()
                if "Gepland" in text or "Scheduled" in text:
                    print(f"  Found 'Gepland' tab: '{text}'")
                    cls = tab.get_attribute("class") or ""
                    tag = get_tag_name(tab)
                    findings.append(f"- **'Gepland' tab tag:** `{tag}`\n")
                    findings.append(f"- **'Gepland' tab text:** `{text}`\n")
                    findings.append(f"- **'Gepland' tab class:** `{cls}`\n")
                    tab.click()
                    page.wait_for_timeout(2000)
                    gepland_found = True

                    # Dump structure of Gepland tab content
                    findings.append(f"\n### Gepland Tab Content\n")
                    gepland_cards = page.query_selector_all("[class*='item'], [class*='card'], [class*='booking']")
                    findings.append(f"- **Cards under Gepland:** {len(gepland_cards)}\n")
                    if gepland_cards:
                        for gc in gepland_cards[:2]:
                            try:
                                cls = gc.get_attribute("class") or ""
                                text = ((gc.inner_text() or "")[:100]).replace("\n", " | ")
                                findings.append(f"  - Card class: `{cls}`, text: {text}\n")
                            except Exception:
                                pass

                    break
            except Exception:
                continue

        print(f"  'Gepland' tab found: {gepland_found}")

        # === EXTRACT ALL CLASS NAMES ===
        print("\nStep 8: Extracting all unique class names...")
        findings.append("\n## All Unique Class Names on Page\n")

        all_classes = set()
        all_elements = page.query_selector_all("*[class]")
        for el in all_elements:
            try:
                cls = el.get_attribute("class") or ""
                if cls:
                    for c in cls.split():
                        all_classes.add(c)
            except Exception:
                continue

        findings.append(f"\n**Total unique classes:** {len(all_classes)}\n\n")
        findings.append("```")
        for c in sorted(all_classes):
            findings.append(f"- `{c}`")
        findings.append("```\n")

        # === EXTRACT ALL ID ATTRIBUTES ===
        print("\nStep 9: Extracting all ID attributes...")
        findings.append("\n## All ID Attributes on Page\n")

        all_ids = []
        all_id_elements = page.query_selector_all("*[id]")
        for el in all_id_elements:
            try:
                attr_id = el.get_attribute("id") or ""
                if attr_id:
                    tag = get_tag_name(el)
                    cls = el.get_attribute("class") or ""
                    all_ids.append(f"{tag}#{attr_id} ({cls})")
            except Exception:
                continue

        findings.append(f"\n**Total elements with IDs:** {len(all_ids)}\n\n")
        findings.append("```")
        for aid in all_ids:
            findings.append(f"- `{aid}`")
        findings.append("```\n")

        browser.close()

    # === WRITE DOM_REFERENCE.md ===
    print("\nStep 10: Writing DOM_REFERENCE.md...")

    # Build the reference document
    reference_content = f"""# DOM Reference — 2Park Dashboard

**Generated:** 2026-05-12
**Source:** mijn.2park.nl
**Screenshot:** {SCREENSHOT_PATH}

## Summary

This document contains the actual DOM structure of the 2Park dashboard as
captured during a live session. Use these selectors for automation scripts.

---

"""
    reference_content += "\n".join(findings)

    with open(REFERENCE_FILE, "w") as f:
        f.write(reference_content)

    print(f"  DOM_REFERENCE.md written to {REFERENCE_FILE}")
    print(f"  File size: {REFERENCE_FILE.stat().st_size} bytes")

    print("\n✅ DOM audit complete!")


if __name__ == "__main__":
    main()
