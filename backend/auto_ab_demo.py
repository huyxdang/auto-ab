from __future__ import annotations

import copy
import json
import math
import os
from dataclasses import dataclass
from email.parser import BytesParser
from email.policy import default
from html import escape
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen


TARGET_CUSTOMER = (
    "small businesses, indie founders, agencies, and e-commerce brands "
    "that see drop-offs but do not know what to change"
)

DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
DEFAULT_WEBSITE_HTML = PROJECT_ROOT / "website2" / "index.html"
VARIANT_B_HTML = PROJECT_ROOT / "website2" / "variant-b.html"


DEMO_WEBSITE: dict[str, Any] = {
    "id": "demo-saas-homepage",
    "version": "A",
    "goal": "structured page that an LLM can edit",
    "conversion_goal": "start_free_trial",
    "target_customer": TARGET_CUSTOMER,
    "sections": [
        {
            "id": "hero",
            "type": "hero",
            "headline": "Turn visitor behavior into better landing pages",
            "subheadline": (
                "Auto AB analyzes heatmaps, clicks, scroll depth, and session "
                "recordings, then generates conversion-focused page variants."
            ),
            "primary_cta": "Start optimizing",
            "secondary_cta": "See demo",
            "friction_risk": "CTA competes with a secondary action and the outcome is abstract.",
        },
        {
            "id": "features",
            "type": "features",
            "headline": "Everything you need to close the optimization loop",
            "items": [
                "Synthetic or real user behavior data",
                "LLM friction analysis",
                "Editable website JSON variants",
                "Predicted A/B test lift",
            ],
            "friction_risk": "Feature list explains mechanics before proving business value.",
        },
        {
            "id": "pricing",
            "type": "pricing",
            "headline": "Simple pricing for growing teams",
            "plans": [
                {
                    "name": "Starter",
                    "price": "$29/mo",
                    "description": "For one website and weekly optimization reports.",
                    "cta": "Choose Starter",
                },
                {
                    "name": "Growth",
                    "price": "$99/mo",
                    "description": "For teams running continuous variant generation.",
                    "cta": "Choose Growth",
                },
            ],
            "friction_risk": "Pricing appears before enough confidence-building proof.",
        },
        {
            "id": "cta",
            "type": "cta",
            "headline": "Let your website decide what to change next",
            "body": "Run the demo loop with simulated visitors, then connect real analytics.",
            "primary_cta": "Generate my first variant",
            "friction_risk": "Final CTA is stronger than the hero CTA, so intent may arrive late.",
        },
    ],
}


SIMULATED_USER_DATA: dict[str, Any] = {
    "sample_size": 320,
    "heatmap_points": [
        {"section": "hero", "x": 426, "y": 218, "intensity": 0.88},
        {"section": "hero", "x": 713, "y": 332, "intensity": 0.62},
        {"section": "features", "x": 288, "y": 812, "intensity": 0.54},
        {"section": "features", "x": 904, "y": 936, "intensity": 0.41},
        {"section": "pricing", "x": 520, "y": 1398, "intensity": 0.36},
        {"section": "cta", "x": 604, "y": 1884, "intensity": 0.21},
    ],
    "scroll_depth": {
        "25_percent": 0.92,
        "50_percent": 0.64,
        "75_percent": 0.39,
        "100_percent": 0.18,
        "average_percent": 57,
    },
    "clicks": [
        {"section": "hero", "target": "secondary_cta", "count": 42},
        {"section": "hero", "target": "primary_cta", "count": 31},
        {"section": "features", "target": "feature_item", "count": 18},
        {"section": "pricing", "target": "starter_cta", "count": 9},
        {"section": "pricing", "target": "growth_cta", "count": 4},
        {"section": "cta", "target": "primary_cta", "count": 6},
    ],
    "drop_off_section": {
        "section": "features",
        "drop_off_rate": 0.31,
        "likely_reason": "Users understand the category but do not yet see a specific payoff.",
    },
}


FAKE_SESSION_RECORDING: list[dict[str, Any]] = [
    {"timestamp_ms": 0, "event": "page_view", "cursor": {"x": 602, "y": 118}, "scroll_y": 0},
    {"timestamp_ms": 850, "event": "cursor_move", "cursor": {"x": 512, "y": 274}, "scroll_y": 0},
    {"timestamp_ms": 1780, "event": "hover", "target": "hero.secondary_cta", "cursor": {"x": 681, "y": 352}, "scroll_y": 0},
    {"timestamp_ms": 2460, "event": "click", "target": "hero.secondary_cta", "cursor": {"x": 681, "y": 352}, "scroll_y": 0},
    {"timestamp_ms": 4120, "event": "scroll", "cursor": {"x": 742, "y": 582}, "scroll_y": 520},
    {"timestamp_ms": 6350, "event": "cursor_move", "cursor": {"x": 303, "y": 760}, "scroll_y": 760},
    {"timestamp_ms": 8290, "event": "scroll", "cursor": {"x": 812, "y": 698}, "scroll_y": 1040},
    {"timestamp_ms": 11140, "event": "rage_scroll", "cursor": {"x": 824, "y": 624}, "scroll_y": 1320},
    {"timestamp_ms": 14320, "event": "scroll", "cursor": {"x": 612, "y": 578}, "scroll_y": 1710},
    {"timestamp_ms": 16840, "event": "hover", "target": "pricing.starter_cta", "cursor": {"x": 519, "y": 591}, "scroll_y": 1280},
    {"timestamp_ms": 19750, "event": "exit", "cursor": {"x": 1198, "y": 12}, "scroll_y": 1390},
]


@dataclass(frozen=True)
class FrictionSignal:
    section: str
    severity: str
    evidence: str
    recommendation: str


class PageTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.elements: list[dict[str, Any]] = []
        self._current: dict[str, Any] | None = None
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag in {"title", "h1", "h2", "h3", "p", "a", "button", "li"}:
            self._current = {"tag": tag, "text": "", "attrs": dict(attrs)}

    def handle_data(self, data: str) -> None:
        if self._skip_depth or self._current is None:
            return
        self._current["text"] += data

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth or self._current is None:
            return
        if tag != self._current["tag"]:
            return
        text = " ".join(self._current["text"].split())
        if text:
            if tag == "title":
                self.title = text
            else:
                self.elements.append(
                    {
                        "tag": tag,
                        "text": text,
                        "href": self._current["attrs"].get("href"),
                    }
                )
        self._current = None


def analyze_website(
    website: dict[str, Any],
    user_data: dict[str, Any],
    target_customer: str,
    session_recording: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Analyze website behavior with OpenAI when configured, else use fallback rules."""
    session_recording = session_recording or []
    llm_result = _analyze_website_with_openai(
        website,
        user_data,
        target_customer,
        session_recording,
    )
    if llm_result is not None:
        return llm_result

    return _analyze_website_with_rules(website, user_data, target_customer, session_recording)


def optimize_html_document(
    html: str,
    target_customer: str = TARGET_CUSTOMER,
    user_data: dict[str, Any] | None = None,
    session_recording: list[dict[str, Any]] | None = None,
    page_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    website = deconstruct_html_document(html, target_customer)
    if page_context:
        website["page_context"] = page_context
    user_data = user_data or simulate_behavior_for_website(website)
    session_recording = session_recording or simulate_session_for_website(website)
    analysis = analyze_website(website, user_data, target_customer, session_recording)
    variant_model = generate_improved_variant(website, analysis)
    improved_html = generate_improved_html(html, website, variant_model, analysis)
    ab_result = simulate_ab_result(website, variant_model, analysis)

    return {
        "input_type": "html",
        "target_customer": target_customer,
        "deconstructed_page": website,
        "simulated_user_data": user_data,
        "fake_session_recording": session_recording,
        "page_context": page_context or {},
        "llm_analysis": analysis,
        "variant_page_model": variant_model,
        "improved_html": improved_html,
        "simulated_ab_result": ab_result,
    }


def optimize_default_website(target_customer: str = TARGET_CUSTOMER) -> dict[str, Any]:
    if not DEFAULT_WEBSITE_HTML.exists():
        return {
            "error": "default_website_not_found",
            "expected_path": str(DEFAULT_WEBSITE_HTML),
        }
    html = DEFAULT_WEBSITE_HTML.read_text(encoding="utf-8")
    result = optimize_html_document(html=html, target_customer=target_customer)
    result["source_file"] = str(DEFAULT_WEBSITE_HTML)
    write_website_outputs(result)
    return result


def write_website_outputs(result: dict[str, Any]) -> None:
    improved_html = result.get("improved_html")
    if not isinstance(improved_html, str) or not improved_html.strip():
        return
    VARIANT_B_HTML.parent.mkdir(parents=True, exist_ok=True)
    VARIANT_B_HTML.write_text(improved_html, encoding="utf-8")


def _optimize_payload_and_write_files(
    html: str,
    target_customer: str,
    user_data: dict[str, Any] | None = None,
    session_recording: list[dict[str, Any]] | None = None,
    page_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = optimize_html_document(
        html=html,
        target_customer=target_customer,
        user_data=user_data,
        session_recording=session_recording,
        page_context=page_context,
    )
    write_website_outputs(result)
    return result


def _fetch_url_html(url: str, timeout: float = 10.0) -> str:
    import ssl
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("URL must start with http:// or https://")
    req = Request(url, headers={"User-Agent": "auto-ab/1.0 (+https://github.com/huyxdang/auto-ab)"})
    ctx = ssl._create_unverified_context()
    with urlopen(req, timeout=timeout, context=ctx) as response:
        raw = response.read(2_000_000)
        charset = response.headers.get_content_charset() or "utf-8"
    return raw.decode(charset, errors="replace")


def _demo_target_html_for_url(url: str) -> str | None:
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    path = (parsed.path or "").lower()
    looks_like_demo = (
        parsed.scheme == "local"
        or "website2" in path
        or "trycloudflare.com" in host
        or host in {"localhost", "127.0.0.1"}
    )
    if looks_like_demo and DEFAULT_WEBSITE_HTML.exists():
        return DEFAULT_WEBSITE_HTML.read_text(encoding="utf-8")
    return None


def _first_section_headline(website: dict[str, Any]) -> str:
    for section in website.get("sections", []) or []:
        headline = section.get("headline") or section.get("label")
        if headline:
            return str(headline)
    return website.get("title") or "Landing page"


def _adapt_for_frontend(result: dict[str, Any], url: str, analytics_source: str = "simulated") -> dict[str, Any]:
    analysis = result.get("llm_analysis", {}) or {}
    ab = result.get("simulated_ab_result", {}) or {}
    user_data = result.get("simulated_user_data", {}) or {}
    session_recording = result.get("fake_session_recording", []) or []
    variant_a = result.get("deconstructed_page") or result.get("demo_website_json") or result.get("variant_a") or {}
    variant_b = result.get("variant_page_model") or result.get("improved_variant_json") or result.get("variant_b") or {}
    lift = float(ab.get("predicted_conversion_lift") or 0.0)
    lift_pct = round(lift * 100)

    pain_points = []
    for point in analysis.get("friction_points", []) or []:
        evidence = str(point.get("evidence") or "")
        pain_points.append({
            "section": str(point.get("section") or "page").title(),
            "type": _friction_type(point),
            "severity": str(point.get("severity") or "medium"),
            "desc": str(point.get("recommendation") or evidence),
        })

    base_score = 70
    baseline_cvr = (ab.get("variant_a", {}).get("predicted_conversion_rate") or 0.038) * 100
    variant_cvr = (ab.get("variant_b", {}).get("predicted_conversion_rate") or 0.046) * 100
    page_context = result.get("page_context", {}) or variant_a.get("page_context", {}) or {}
    if _is_website2_context(page_context, variant_a):
        baseline_site = _website2_preview_site("control")
        variant_site = _website2_preview_site("variant", analysis.get("recommendations", []), variant_b)
    else:
        baseline_site = _website_to_preview_site(variant_a, "control")
        variant_site = _website_to_preview_site(variant_b, "variant", analysis.get("recommendations", []))
    variants = _build_variant_candidates(variant_b, variant_site, analysis, lift_pct, base_score, variant_cvr)

    return {
        "url": url,
        "analyticsSource": _analytics_source_label(analytics_source),
        "sourceMode": "sandbox_simulation" if analytics_source == "simulated" else "simulated_connector_preview",
        "behavior": _behavior_for_frontend(user_data, session_recording, variant_a),
        "painPoints": pain_points,
        "diagnosis": {
            "summary": analysis.get("summary", "Behavior data surfaced conversion friction before variant generation."),
            "frictionPoints": analysis.get("friction_points", []) or [],
            "recommendations": analysis.get("recommendations", []) or [],
        },
        "baseline": {
            "headline": _first_section_headline(variant_a),
            "score": base_score,
            "cvr": f"{baseline_cvr:.1f}%",
            "site": baseline_site,
        },
        "variant": {
            "headline": _first_section_headline(variant_b),
            "score": min(99, round(base_score * (1 + lift))),
            "cvr": f"{variant_cvr:.1f}%",
            "changes": list(analysis.get("recommendations", []) or [])[:4],
            "hypothesis": (analysis.get("recommendations", []) or ["Focus the page around one clearer conversion path."])[0],
            "uplift": f"{'+' if lift >= 0 else ''}{lift_pct}%",
            "liftPct": lift_pct,
            "site": variant_site,
        },
        "variants": variants,
        "uplift": f"{'+' if lift >= 0 else ''}{lift_pct}%",
        "test": {
            "winner": "B",
            "confidence": ab.get("confidence", "medium"),
            "predictedLift": f"{'+' if lift >= 0 else ''}{lift_pct}%",
            "interpretation": ab.get("interpretation", "Variant B is predicted to win by resolving the strongest friction signals."),
        },
        "loop": [
            {"key": "ingest", "label": "Ingest behavior", "status": "complete"},
            {"key": "diagnose", "label": "Diagnose friction", "status": "complete"},
            {"key": "generate", "label": "Generate variant", "status": "complete"},
            {"key": "test", "label": "Predict A/B lift", "status": "running"},
        ],
    }


def _analytics_source_label(source: str) -> str:
    return {
        "simulated": "Simulated visitors",
        "posthog": "PostHog",
        "ga4": "Google Analytics 4",
        "hotjar": "Hotjar",
    }.get(source, "Simulated visitors")


def _friction_type(point: dict[str, Any]) -> str:
    text = f"{point.get('section', '')} {point.get('evidence', '')} {point.get('recommendation', '')}".lower()
    if "secondary cta" in text or "primary cta" in text:
        return "CTA hierarchy friction"
    if "drop-off" in text or "drop off" in text:
        return "Drop-off friction"
    if "full page" in text or "underexposed" in text:
        return "Underexposed CTA"
    if "rage" in text or "pricing" in text:
        return "Trust-before-pricing gap"
    if "proof" in text or "trust" in text:
        return "Delayed proof"
    return "Conversion friction"


def _behavior_for_frontend(user_data: dict[str, Any], session_recording: list[dict[str, Any]], website: dict[str, Any]) -> dict[str, Any]:
    sample_size = int(user_data.get("sample_size") or 1247)
    click_total = sum(int(click.get("count", 0)) for click in user_data.get("clicks", []) or [])
    events = max(3891, click_total * 31, sample_size * 3)
    return {
        "sessions": sample_size if sample_size > 1000 else 1247,
        "events": events,
        "averageTimeOnPage": "01:42",
        "bounceRate": "58%",
        "heatmapPoints": user_data.get("heatmap_points", []) or [],
        "scrollDepth": user_data.get("scroll_depth", {}) or {},
        "clicks": user_data.get("clicks", []) or [],
        "dropOff": user_data.get("drop_off_section", {}) or {},
        "elementSignals": _element_signals_for_frontend(user_data, website),
        "recordings": _recordings_for_frontend(session_recording, website),
    }


def _element_signals_for_frontend(user_data: dict[str, Any], website: dict[str, Any]) -> list[dict[str, Any]]:
    if _is_website2_context(website.get("page_context", {}) or {}, website):
        return _website2_element_signals()

    context = website.get("page_context", {}) or {}
    context_elements = context.get("elements") if isinstance(context, dict) else None
    if isinstance(context_elements, list) and context_elements:
        signals = []
        for index, element in enumerate(context_elements[:5]):
            selector = str(element.get("selector") or f"element_{index + 1}")
            severity = "high" if index in {1, 2} else "medium" if index > 2 else "low"
            signals.append({
                "id": _section_id(selector, index + 1),
                "selector": selector,
                "copy": str(element.get("copy") or selector),
                "signal": str(element.get("signal") or _section_signal_label(index, severity)),
                "severity": severity,
                "diagnosis": str(element.get("diagnosis") or _section_diagnosis(selector, severity)),
            })
        return signals

    drop_section = (user_data.get("drop_off_section", {}) or {}).get("section")
    sections = website.get("sections", []) or []
    signals = []
    for index, section in enumerate(sections[:5]):
        section_id = section.get("id", f"section_{index + 1}")
        severity = "high" if section_id == drop_section else "medium" if index > 1 else "low"
        headline = section.get("headline") or section.get("label") or "Page section"
        signals.append({
            "id": section_id,
            "selector": f"#{section_id}",
            "copy": headline,
            "signal": _section_signal_label(index, severity),
            "severity": severity,
            "diagnosis": _section_diagnosis(section_id, severity),
        })
    return signals


def _website2_element_signals() -> list[dict[str, Any]]:
    return [
        {
            "id": "hero",
            "selector": ".hero-copy h1",
            "copy": "Build and ship an AI agent in 1 day.",
            "signal": "82% viewport attention",
            "severity": "low",
            "diagnosis": "Strong promise. Keep it, but make the next-session outcome clearer.",
        },
        {
            "id": "status",
            "selector": ".facts .status-closed",
            "copy": "Registration Closed",
            "signal": "38% exits after noticing",
            "severity": "high",
            "diagnosis": "Closed status creates dead-end anxiety before the fallback CTA is clear.",
        },
        {
            "id": "waitlist",
            "selector": "#waitlist",
            "copy": "Enter email for next event waitlist",
            "signal": "14 rage-click clusters",
            "severity": "high",
            "diagnosis": "Waitlist fallback is useful but visually feels secondary to the closed event.",
        },
        {
            "id": "luma",
            "selector": "[data-cta=\"luma\"]",
            "copy": "View Luma Event",
            "signal": "23% intent leakage",
            "severity": "medium",
            "diagnosis": "Secondary event link pulls users away from the conversion path.",
        },
        {
            "id": "judges",
            "selector": "#judges",
            "copy": "Track judges",
            "signal": "High trust, low reach",
            "severity": "medium",
            "diagnosis": "Credibility is strong but appears too late for hesitant visitors.",
        },
    ]


def _section_signal_label(index: int, severity: str) -> str:
    if severity == "high":
        return "38% exits after noticing"
    if severity == "medium":
        return "High intent, low reach"
    return f"{max(48, 82 - index * 9)}% viewport attention"


def _section_diagnosis(section_id: str, severity: str) -> str:
    if severity == "high":
        return "Visitors hesitate here before the conversion path feels safe or specific."
    if "hero" in section_id:
        return "Strong first attention. Preserve the promise while making the next action clearer."
    return "Useful content, but it needs stronger sequencing before the primary CTA."


def _recordings_for_frontend(session_recording: list[dict[str, Any]], website: dict[str, Any]) -> list[dict[str, Any]]:
    sections = [section.get("id", f"section_{index + 1}") for index, section in enumerate(website.get("sections", []) or [])]
    hotspot = sections[1] if len(sections) > 1 else sections[0] if sections else "hero"
    return [
        {
            "id": "#sess_8a2f",
            "user": "Visitor - United States",
            "duration": "02:14",
            "dropoff": f"Bounced near {hotspot}",
            "severity": "high",
            "scroll": 62,
            "hotspot": hotspot,
            "path": _recording_path(sections, 62),
        },
        {
            "id": "#sess_b91c",
            "user": "Visitor - Germany",
            "duration": "01:38",
            "dropoff": "Clicked secondary path",
            "severity": "high",
            "scroll": 41,
            "hotspot": sections[0] if sections else "hero",
            "path": _recording_path(sections, 41),
        },
        {
            "id": "#sess_4d77",
            "user": "Visitor - India",
            "duration": "00:52",
            "dropoff": "Left after hero scan",
            "severity": "medium",
            "scroll": 18,
            "hotspot": sections[0] if sections else "hero",
            "path": _recording_path(sections[:2], 18),
        },
    ]


def _recording_path(sections: list[str], scroll: int) -> list[dict[str, Any]]:
    if not sections:
        sections = ["hero", "cta"]
    path = []
    for index, section_id in enumerate(sections[:4]):
        path.append({
            "id": section_id,
            "label": f"Viewed {section_id.replace('-', ' ')}",
            "x": 22 + index * 14,
            "y": min(86, 24 + index * max(10, scroll // 4)),
        })
    path.append({"id": "exit", "label": "Exited without converting", "x": 72, "y": 82})
    return path


def _is_website2_context(page_context: dict[str, Any], website: dict[str, Any]) -> bool:
    source_file = str(page_context.get("sourceFile") or page_context.get("source_file") or "")
    title = str(website.get("title") or "")
    return "website2" in source_file or "AI Hackathon Weekend Build with Codex" in title


def _website2_preview_site(tone: str, changes: list[str] | None = None, variant: dict[str, Any] | None = None) -> dict[str, Any]:
    if tone == "variant":
        headline = _first_section_headline(variant or {})
        if not headline or headline == "Landing page":
            headline = "Join the next Codex sprint and ship your first AI agent in one day"
        return {
            "brand": "Codex Community Vietnam",
            "navCta": "Join next cohort",
            "eyebrow": "Next Codex sprint - HCMC waitlist now open",
            "status": "Next cohort waitlist is live - first invites release soon",
            "headline": headline if headline != "Join the next Codex sprint and ship your first AI agent in one day" else "Get the Codex launch kit before the next build sprint opens",
            "subheadline": "Sold-out traffic now lands on a high-intent offer: setup guide, CAR templates, judge criteria, and team matching before registration reopens.",
            "primaryCta": "Claim next-cohort invite",
            "secondaryCta": "Preview shipped agents",
            "sideTitle": "Cohort Launch Kit",
            "sideCopy": "The poster becomes proof. The generated page sells a live next action instead of replaying a closed event.",
            "posterTag": "Generated Variant",
            "trust": ["175 builders registered", "Sold out fast", "3 build tracks", "Judges from Scale, Depth, Impact"],
            "facts": [
                {"value": "Next", "label": "Cohort waitlist"},
                {"value": "HCMC", "label": "Local build session"},
                {"value": "Open", "label": "Early invite status"},
            ],
            "proof": ["Setup guide unlocked", "CAR templates included", "Team matching before launch"],
            "modules": ["Invite ladder replaces dead-end status", "Proof rail promoted above agenda", "Luma/GitHub moved to resource drawer"],
            "experiments": ["Next test: launch kit vs cohort headline", "Mobile sticky invite bar", "Judge proof carousel"],
            "stickyCta": "Sticky mobile bar: Claim invite + get setup guide",
            "fullPagePath": "/auto-ab/generated/variant-b.html",
            "changes": list(changes or [])[:5] or [
                "Closed status converted into a live next-cohort invite ladder",
                "Hero offer changed from attending a closed event to claiming a launch kit",
                "Poster demoted into proof so the form owns the visual hierarchy",
                "Luma and GitHub links moved into a resource drawer after email capture",
                "Next loop will test sticky mobile invite bar and judge-proof carousel",
            ],
        }

    return {
        "brand": "Codex Community Vietnam",
        "navCta": "Join waitlist",
        "eyebrow": "AI Hackathon - Weekend Build with Codex and CAR",
        "status": "Closed - waitlist open",
        "headline": "Build and ship an AI agent in 1 day.",
        "subheadline": "A hands-on Ho Chi Minh City build session for engineers, founders, and operators learning practical agentic engineering with OpenAI Codex and Codex Auto Runner.",
        "primaryCta": "Join waitlist",
        "secondaryCta": "View Luma Event",
        "sideTitle": "Codex Auto Runner",
        "sideCopy": "Official Luma event poster dominates the hero while conversion actions compete below the fold.",
        "posterTag": "Event Poster",
        "trust": ["175 builders going", "Sold out fast", "3 build tracks"],
        "facts": [
            {"value": "May 09", "label": "Event date"},
            {"value": "HCMC", "label": "Local build session"},
            {"value": "Closed", "label": "Registration status", "tone": "closed"},
        ],
        "proof": ["1 day from concept to demo", "175 builders registered", "3 tracks"],
        "modules": ["Agenda below fold", "Judges lower down", "Footer repeats waitlist"],
        "experiments": [],
    }


def _website_to_preview_site(website: dict[str, Any], tone: str, changes: list[str] | None = None) -> dict[str, Any]:
    sections = website.get("sections", []) or []
    hero = sections[0] if sections else {}
    cta_section = next((section for section in sections if section.get("type") == "cta"), sections[-1] if sections else {})
    ctas = hero.get("ctas", []) or []
    primary_cta = hero.get("primary_cta") or (ctas[0].get("text") if ctas else "Start now")
    secondary_cta = hero.get("secondary_cta") or (ctas[1].get("text") if len(ctas) > 1 else "Learn more")
    title = website.get("title") or _first_section_headline(website)
    return {
        "brand": _brand_from_title(title),
        "navCta": primary_cta,
        "eyebrow": "Behavior-informed variant" if tone == "variant" else "Current control page",
        "status": "Generated from friction diagnosis" if tone == "variant" else "Original page from URL",
        "headline": hero.get("headline") or title,
        "subheadline": _section_body_text(hero) or "Page copy parsed from the submitted URL.",
        "primaryCta": primary_cta,
        "secondaryCta": secondary_cta,
        "sideTitle": "Generated Treatment" if tone == "variant" else "Control Experience",
        "sideCopy": "AI changed page emphasis based on visitor behavior signals." if tone == "variant" else "Baseline page before behavior-informed changes.",
        "posterTag": "Generated Variant" if tone == "variant" else "Original Website",
        "trust": _preview_trust(sections),
        "facts": _preview_facts(tone),
        "proof": _preview_proof(sections),
        "modules": [section.get("headline") or section.get("id", "Section") for section in sections[1:4]] or ["Hero", "CTA", "Proof"],
        "changes": list(changes or [])[:5],
    }


def _section_body_text(section: dict[str, Any]) -> str:
    body = section.get("subheadline") or section.get("body") or ""
    if isinstance(body, list):
        return " ".join(str(item) for item in body[:2])[:220]
    return str(body)[:220]


def _brand_from_title(title: str) -> str:
    clean = " ".join(str(title).split())
    if not clean:
        return "Submitted Website"
    return clean[:34]


def _preview_trust(sections: list[dict[str, Any]]) -> list[str]:
    items: list[str] = []
    for section in sections:
        for item in section.get("items", []) or []:
            if len(items) < 4:
                items.append(str(item)[:42])
    return items or ["Real page structure parsed", "Behavior signals mapped", "Variant generated"]


def _preview_facts(tone: str) -> list[dict[str, str]]:
    if tone == "variant":
        return [
            {"value": "AI", "label": "Generated treatment"},
            {"value": "Open", "label": "Next test status"},
            {"value": "Lift", "label": "Predicted outcome"},
        ]
    return [
        {"value": "A", "label": "Control"},
        {"value": "Live", "label": "Current URL"},
        {"value": "Base", "label": "Conversion path"},
    ]


def _preview_proof(sections: list[dict[str, Any]]) -> list[str]:
    names = [section.get("headline") for section in sections if section.get("headline")]
    return [str(name)[:42] for name in names[1:4]] or ["Page parsed", "Signals clustered", "Recommendation ready"]


def _build_variant_candidates(
    variant_b: dict[str, Any],
    variant_site: dict[str, Any],
    analysis: dict[str, Any],
    lift_pct: int,
    base_score: int,
    variant_cvr: float,
) -> list[dict[str, Any]]:
    recs = list(analysis.get("recommendations", []) or [])
    headline = _first_section_headline(variant_b)
    variant_b_card = {
        "label": "B",
        "hypothesis": recs[0] if recs else "Make the primary conversion path clearer above the fold.",
        "headline": headline,
        "score": min(99, round(base_score * (1 + lift_pct / 100))),
        "cvr": f"{variant_cvr:.1f}%",
        "uplift": f"+{lift_pct}%",
        "liftPct": lift_pct,
        "changes": recs[:3] or variant_site.get("changes", [])[:3],
        "site": variant_site,
    }
    alt_lift = max(3, lift_pct - 7)
    alt_site = copy.deepcopy(variant_site)
    alt_site["headline"] = _alternate_headline(headline)
    alt_site["posterTag"] = "Alternate Variant"
    variant_c_card = {
        "label": "C",
        "hypothesis": recs[1] if len(recs) > 1 else "Move proof earlier before asking for commitment.",
        "headline": alt_site["headline"],
        "score": min(99, round(base_score * (1 + alt_lift / 100))),
        "cvr": f"{variant_cvr * (1 - max(0.03, (lift_pct - alt_lift) / 100)):.1f}%",
        "uplift": f"+{alt_lift}%",
        "liftPct": alt_lift,
        "changes": recs[2:5] or recs[:2] or variant_site.get("changes", [])[:2],
        "site": alt_site,
    }
    return [variant_b_card, variant_c_card]


def _alternate_headline(headline: str) -> str:
    if not headline:
        return "Turn visitor friction into the next better page"
    return headline.rstrip(".") + " with less visitor hesitation"


def deconstruct_html_document(html: str, target_customer: str = TARGET_CUSTOMER) -> dict[str, Any]:
    parser = PageTextParser()
    parser.feed(html)
    elements = parser.elements
    sections = _elements_to_sections(elements)

    return {
        "id": "uploaded-html-page",
        "version": "A",
        "source_type": "html",
        "title": parser.title or _first_text(elements, {"h1", "h2"}) or "Uploaded HTML page",
        "goal": "optimize this HTML page for conversion",
        "conversion_goal": "primary_cta_click",
        "target_customer": target_customer,
        "sections": sections,
    }


def simulate_behavior_for_website(website: dict[str, Any]) -> dict[str, Any]:
    sections = website.get("sections", [])
    section_count = max(len(sections), 1)
    heatmap_points = []
    clicks = []
    for index, section in enumerate(sections):
        section_id = section.get("id", f"section_{index + 1}")
        attention = max(0.18, 0.9 - index * 0.16)
        heatmap_points.append(
            {
                "section": section_id,
                "x": 360 + (index % 3) * 180,
                "y": 220 + index * 420,
                "intensity": round(attention, 2),
            }
        )
        if section.get("ctas"):
            clicks.append(
                {
                    "section": section_id,
                    "target": "primary_cta",
                    "count": max(3, int(34 * attention)),
                }
            )

    drop_index = min(1, section_count - 1)
    drop_section = sections[drop_index].get("id", "section_1") if sections else "section_1"
    return {
        "sample_size": 320,
        "heatmap_points": heatmap_points,
        "scroll_depth": {
            "25_percent": 0.91,
            "50_percent": 0.62,
            "75_percent": 0.37,
            "100_percent": 0.19,
            "average_percent": 56,
        },
        "clicks": clicks or [{"section": "hero", "target": "page_body", "count": 22}],
        "drop_off_section": {
            "section": drop_section,
            "drop_off_rate": 0.29 + min(0.12, section_count * 0.01),
            "likely_reason": "Visitors show early interest but lose momentum before the final conversion action.",
        },
    }


def simulate_session_for_website(website: dict[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = [
        {"timestamp_ms": 0, "event": "page_view", "cursor": {"x": 620, "y": 120}, "scroll_y": 0}
    ]
    for index, section in enumerate(website.get("sections", [])):
        scroll_y = index * 520
        events.append(
            {
                "timestamp_ms": 1000 + index * 2600,
                "event": "scroll",
                "cursor": {"x": 680 - index * 24, "y": 560},
                "scroll_y": scroll_y,
                "section": section.get("id", f"section_{index + 1}"),
            }
        )
        if section.get("ctas"):
            events.append(
                {
                    "timestamp_ms": 2100 + index * 2600,
                    "event": "hover",
                    "target": f"{section.get('id')}.primary_cta",
                    "cursor": {"x": 520, "y": 610},
                    "scroll_y": scroll_y,
                }
            )
    events.append(
        {
            "timestamp_ms": 14500,
            "event": "exit",
            "cursor": {"x": 1188, "y": 18},
            "scroll_y": max(700, len(website.get("sections", [])) * 390),
        }
    )
    return events


def _analyze_website_with_rules(
    website: dict[str, Any],
    user_data: dict[str, Any],
    target_customer: str,
    session_recording: list[dict[str, Any]],
) -> dict[str, Any]:
    sections = {section["id"]: section for section in website.get("sections", [])}
    click_counts = _click_counts_by_target(user_data.get("clicks", []))
    drop_off = user_data.get("drop_off_section", {})
    scroll_depth = user_data.get("scroll_depth", {})
    friction_points: list[FrictionSignal] = []

    hero_secondary = click_counts.get(("hero", "secondary_cta"), 0)
    hero_primary = click_counts.get(("hero", "primary_cta"), 0)
    if hero_secondary >= hero_primary:
        friction_points.append(
            FrictionSignal(
                section="hero",
                severity="high",
                evidence=(
                    f"Hero secondary CTA received {hero_secondary} clicks versus "
                    f"{hero_primary} primary CTA clicks."
                ),
                recommendation=(
                    "Make the primary action more concrete and reduce the visual weight "
                    "of the secondary action."
                ),
            )
        )

    if drop_off.get("section") in sections:
        friction_points.append(
            FrictionSignal(
                section=drop_off["section"],
                severity="high" if drop_off.get("drop_off_rate", 0) >= 0.3 else "medium",
                evidence=(
                    f"{drop_off.get('drop_off_rate', 0):.0%} drop-off around "
                    f"the {drop_off['section']} section. {drop_off.get('likely_reason', '')}"
                ),
                recommendation=(
                    "Lead with the pain and outcome before listing product mechanics."
                ),
            )
        )

    if scroll_depth.get("100_percent", 0) < 0.25:
        friction_points.append(
            FrictionSignal(
                section="cta",
                severity="medium",
                evidence=(
                    f"Only {scroll_depth.get('100_percent', 0):.0%} of visitors reach "
                    "the full page, so the strongest CTA is underexposed."
                ),
                recommendation=(
                    "Move the strongest CTA language into the hero and repeat proof "
                    "before pricing."
                ),
            )
        )

    if any(event.get("event") == "rage_scroll" for event in session_recording):
        friction_points.append(
            FrictionSignal(
                section="pricing",
                severity="medium",
                evidence="Session recording includes a rapid scroll before pricing.",
                recommendation=(
                    "Add trust-building proof before pricing so users do not meet cost "
                    "before value."
                ),
            )
        )

    return {
        "provider": "fallback_rules",
        "target_customer": target_customer,
        "summary": (
            "Visitors show interest in the category, but the page delays the clearest "
            "business outcome and splits early CTA intent."
        ),
        "friction_points": [signal.__dict__ for signal in friction_points],
        "recommendations": [
            "Rewrite the hero around a specific promise: identify drop-offs and generate the next test.",
            "Reorder features so the first items map to customer pain, not implementation details.",
            "Add confidence before pricing with proof-oriented copy.",
            "Use one dominant CTA across hero and final CTA.",
        ],
    }


def generate_improved_variant(website: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
    llm_variant = _generate_variant_with_openai(website, analysis)
    if llm_variant is not None:
        return llm_variant

    return _generate_variant_with_rules(website, analysis)


def _generate_variant_with_rules(website: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
    variant = copy.deepcopy(website)
    variant["version"] = "B"
    variant["generated_from"] = website.get("version", "A")
    variant["optimization_summary"] = analysis["summary"]
    variant["provider"] = "fallback_rules"

    sections = {section["id"]: section for section in variant.get("sections", [])}
    if {"hero", "features", "pricing", "cta"}.issubset(sections):
        sections["hero"].update(
            {
                "headline": "Find why visitors leave, then launch the next better page",
                "subheadline": (
                    "Auto AB turns behavior data into friction insights, editable page JSON, "
                    "and a predicted A/B result before you spend weeks testing guesses."
                ),
                "primary_cta": "Generate my first variant",
                "secondary_cta": "View behavior analysis",
                "change_reason": "Clarifies the business outcome and aligns hero CTA with the final CTA.",
            }
        )
        sections["features"].update(
            {
                "headline": "From behavior data to the next page version",
                "items": [
                    "Spot where visitors hesitate, click, scroll, and leave",
                    "Convert friction into prioritized recommendations",
                    "Rewrite hero, features, pricing, and CTA sections as structured JSON",
                    "Predict the conversion lift before launching the A/B test",
                ],
                "change_reason": "Frames features as a workflow that solves the target customer's pain.",
            }
        )
        sections["pricing"].update(
            {
                "headline": "Start with one optimization loop",
                "proof": "Designed for teams that have traffic data but no dedicated conversion team.",
                "plans": [
                    {
                        "name": "Starter",
                        "price": "$29/mo",
                        "description": "Analyze one site, generate variants, and export page JSON.",
                        "cta": "Start Starter",
                    },
                    {
                        "name": "Growth",
                        "price": "$99/mo",
                        "description": "Continuous analysis, session insights, and weekly A/B recommendations.",
                        "cta": "Start Growth",
                    },
                ],
                "change_reason": "Adds fit and proof before the purchase decision.",
            }
        )
        sections["cta"].update(
            {
                "headline": "Stop guessing what to change next",
                "body": "Run the full optimization loop with simulated data today, then connect real behavior data when traffic arrives.",
                "primary_cta": "Generate my first variant",
                "change_reason": "Repeats a single decisive action.",
            }
        )
    else:
        for section in variant.get("sections", []):
            section["headline"] = _improve_headline(section.get("headline") or section.get("label") or "")
            section["change_reason"] = "Fallback rewrite makes the section outcome clearer."
    return variant


def simulate_ab_result(variant_a: dict[str, Any], variant_b: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
    base_conversion_rate = 0.038
    resolved_high = sum(
        1 for point in analysis.get("friction_points", []) if point.get("severity") == "high"
    )
    resolved_medium = sum(
        1 for point in analysis.get("friction_points", []) if point.get("severity") == "medium"
    )
    lift = 0.08 + resolved_high * 0.055 + resolved_medium * 0.025
    lift = min(lift, 0.31)
    variant_b_rate = base_conversion_rate * (1 + lift)
    sessions_per_variant = 1000

    return {
        "variant_a": {
            "version": variant_a.get("version", "A"),
            "sessions": sessions_per_variant,
            "predicted_conversions": round(sessions_per_variant * base_conversion_rate),
            "predicted_conversion_rate": round(base_conversion_rate, 4),
        },
        "variant_b": {
            "version": variant_b.get("version", "B"),
            "sessions": sessions_per_variant,
            "predicted_conversions": round(sessions_per_variant * variant_b_rate),
            "predicted_conversion_rate": round(variant_b_rate, 4),
        },
        "predicted_conversion_lift": round(lift, 3),
        "confidence": _confidence_from_signal_count(len(analysis.get("friction_points", []))),
        "interpretation": (
            "Variant B is predicted to win because it concentrates early intent on one CTA, "
            "states the outcome sooner, and adds proof before pricing."
        ),
    }


def generate_improved_html(
    original_html: str,
    website: dict[str, Any],
    variant_model: dict[str, Any],
    analysis: dict[str, Any],
) -> str:
    improved = _generate_improved_html_with_openai(original_html, website, variant_model, analysis)
    if improved:
        return improved
    return _render_variant_model_as_html(variant_model)


def build_final_result(
    target_customer: str = TARGET_CUSTOMER,
    website: dict[str, Any] | None = None,
    user_data: dict[str, Any] | None = None,
    session_recording: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    website = website or DEMO_WEBSITE
    user_data = user_data or SIMULATED_USER_DATA
    session_recording = session_recording or FAKE_SESSION_RECORDING
    analysis = analyze_website(website, user_data, target_customer, session_recording)
    variant_b = generate_improved_variant(website, analysis)
    ab_result = simulate_ab_result(website, variant_b, analysis)

    return {
        "demo_website_json": website,
        "simulated_user_data": user_data,
        "fake_session_recording": session_recording,
        "llm_analysis": analysis,
        "improved_variant_json": variant_b,
        "simulated_ab_result": ab_result,
    }


def _analyze_website_with_openai(
    website: dict[str, Any],
    user_data: dict[str, Any],
    target_customer: str,
    session_recording: list[dict[str, Any]],
) -> dict[str, Any] | None:
    prompt_payload = {
        "website_json": website,
        "simulated_user_data": user_data,
        "session_recording": session_recording,
        "target_customer": target_customer,
        "required_output_shape": {
            "provider": "openai",
            "model": "string",
            "target_customer": "string",
            "summary": "string",
            "friction_points": [
                {
                    "section": "hero|features|pricing|cta",
                    "severity": "low|medium|high",
                    "evidence": "specific evidence from data",
                    "recommendation": "specific website change",
                }
            ],
            "recommendations": ["prioritized recommendation strings"],
        },
    }
    result = _call_openai_json(
        system_prompt=(
            "You are a conversion-rate optimization analyst for an autonomous "
            "website optimization product. Analyze behavior data and return only "
            "valid JSON. Ground every friction point in the supplied data. Do not "
            "invent sections outside the website JSON."
        ),
        user_prompt=(
            "Analyze this website JSON and simulated user behavior for the target "
            "customer. Return JSON matching required_output_shape."
        ),
        payload=prompt_payload,
    )
    if not isinstance(result, dict):
        return None

    result["provider"] = "openai"
    result["model"] = _openai_model()
    result.setdefault("target_customer", target_customer)
    result.setdefault("friction_points", [])
    result.setdefault("recommendations", [])
    return result


def _generate_variant_with_openai(
    website: dict[str, Any],
    analysis: dict[str, Any],
) -> dict[str, Any] | None:
    prompt_payload = {
        "website_json": website,
        "analysis": analysis,
        "required_output_shape": {
            "id": "same id as input",
            "version": "B",
            "generated_from": "A",
            "provider": "openai",
            "optimization_summary": "string",
            "sections": [
                {
                    "id": "hero|features|pricing|cta",
                    "type": "same section type",
                    "headline": "rewritten headline",
                    "change_reason": "why this edit addresses analysis",
                }
            ],
        },
    }
    result = _call_openai_json(
        system_prompt=(
            "You are a senior landing-page copy and conversion strategist. Rewrite "
            "the supplied website as editable website JSON. Preserve the same "
            "section ids and types: hero, features, pricing, cta. Return only valid "
            "JSON. Make concrete changes that address the analysis."
        ),
        user_prompt=(
            "Generate improved Variant B website JSON from Variant A and the "
            "analysis. Preserve editable structure and include change_reason fields."
        ),
        payload=prompt_payload,
    )
    if not isinstance(result, dict):
        return None
    result = _unwrap_variant_result(result)

    result.setdefault("id", website.get("id", "demo-saas-homepage"))
    result["version"] = "B"
    result.setdefault("generated_from", website.get("version", "A"))
    result["provider"] = "openai"
    result.setdefault("optimization_summary", analysis.get("summary", ""))
    if "sections" not in result:
        return None
    return result


def _generate_improved_html_with_openai(
    original_html: str,
    website: dict[str, Any],
    variant_model: dict[str, Any],
    analysis: dict[str, Any],
) -> str | None:
    result = _call_openai_json(
        system_prompt=(
            "You are a frontend conversion optimization agent. Return an improved "
            "complete HTML document. Preserve the user's original technology level: "
            "plain HTML in, plain HTML out. Keep the document self-contained and "
            "valid. Do not include markdown."
        ),
        user_prompt=(
            "Rewrite this HTML into Variant B using the analysis and variant page "
            "model. Return JSON with exactly one field: improved_html."
        ),
        payload={
            "original_html": original_html,
            "deconstructed_page": website,
            "analysis": analysis,
            "variant_page_model": variant_model,
            "required_output_shape": {"improved_html": "<!doctype html>..."},
        },
    )
    if not isinstance(result, dict):
        return None
    improved_html = result.get("improved_html")
    if not isinstance(improved_html, str) or "<html" not in improved_html.lower():
        return None
    return improved_html


def _unwrap_variant_result(result: dict[str, Any]) -> dict[str, Any]:
    for key in ("improved_variant_json", "variant_b", "variant", "website_json"):
        nested = result.get(key)
        if isinstance(nested, dict):
            return nested
    return result


def _call_openai_json(system_prompt: str, user_prompt: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    _load_env_file(PROJECT_ROOT / ".env")
    _load_env_file(BACKEND_DIR / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        return None

    try:
        from openai import OpenAI
    except ImportError:
        return None

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.responses.create(
            model=_openai_model(),
            input=[
                {
                    "role": "system",
                    "content": (
                        f"{system_prompt}\n\n"
                        "Important: respond with one JSON object and no markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": f"{user_prompt}\n\n{json.dumps(payload, indent=2)}",
                },
            ],
            text={"format": {"type": "json_object"}},
        )
        output_text = getattr(response, "output_text", "")
        if not output_text:
            return None
        return json.loads(output_text)
    except Exception:
        return None


def _openai_model() -> str:
    return os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _elements_to_sections(elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for element in elements:
        tag = element.get("tag")
        text = element.get("text", "")
        if tag in {"h1", "h2"} or current is None:
            current = {
                "id": _section_id(text, len(sections) + 1),
                "type": _classify_section(text, len(sections)),
                "headline": text if tag in {"h1", "h2", "h3"} else "",
                "body": [],
                "ctas": [],
                "links": [],
            }
            sections.append(current)
            if tag not in {"h1", "h2", "h3"}:
                current["body"].append(text)
            continue

        if tag == "h3" and not current.get("headline"):
            current["headline"] = text
        elif tag in {"a", "button"}:
            item = {"text": text}
            if element.get("href"):
                item["href"] = element["href"]
            current["ctas" if _looks_like_cta(text) else "links"].append(item)
        elif tag == "li":
            current.setdefault("items", []).append(text)
        else:
            current["body"].append(text)

    if not sections:
        return [
            {
                "id": "page",
                "type": "page",
                "headline": "Uploaded HTML page",
                "body": [],
                "ctas": [],
                "links": [],
            }
        ]

    sections[0]["type"] = "hero"
    if sections[-1]["ctas"] or "cta" in sections[-1]["id"]:
        sections[-1]["type"] = "cta"
    return sections


def _render_variant_model_as_html(variant_model: dict[str, Any]) -> str:
    title = escape(variant_model.get("title") or "Optimized page")
    section_html = []
    for section in variant_model.get("sections", []):
        headline = escape(section.get("headline") or section.get("label") or "Section")
        body = section.get("body", [])
        if isinstance(body, str):
            body = [body]
        items = section.get("items", [])
        ctas = section.get("ctas", [])
        if section.get("primary_cta"):
            ctas = [{"text": section["primary_cta"]}, *ctas]

        section_html.append(
            "\n".join(
                [
                    f'<section class="section section-{escape(section.get("type", "content"))}">',
                    f"  <h2>{headline}</h2>",
                    *[f"  <p>{escape(str(paragraph))}</p>" for paragraph in body[:3]],
                    _render_list(items),
                    _render_ctas(ctas),
                    "</section>",
                ]
            )
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; color: #172033; background: #f7f8fa; }}
    main {{ width: min(1040px, calc(100% - 32px)); margin: 0 auto; padding: 40px 0; }}
    .section {{ padding: 36px 0; border-bottom: 1px solid #dde3ea; }}
    .section-hero h2 {{ font-size: clamp(2.4rem, 7vw, 4.5rem); line-height: 1; }}
    h2 {{ margin: 0 0 14px; font-size: clamp(1.7rem, 4vw, 3rem); line-height: 1.08; }}
    p, li {{ font-size: 1.05rem; line-height: 1.65; color: #4b5768; }}
    .actions {{ display: flex; gap: 12px; flex-wrap: wrap; margin-top: 20px; }}
    .button {{ display: inline-block; padding: 12px 18px; border-radius: 8px; background: #0f766e; color: white; text-decoration: none; font-weight: 700; }}
  </style>
</head>
<body>
  <main>
    {''.join(section_html)}
  </main>
</body>
</html>"""


def _render_list(items: Any) -> str:
    if not isinstance(items, list) or not items:
        return ""
    return "\n".join(["  <ul>", *[f"    <li>{escape(str(item))}</li>" for item in items[:8]], "  </ul>"])


def _render_ctas(ctas: Any) -> str:
    if not isinstance(ctas, list) or not ctas:
        return ""
    links = []
    for cta in ctas[:3]:
        if isinstance(cta, dict):
            text = cta.get("text") or cta.get("label") or cta.get("cta")
            href = cta.get("href") or "#"
        else:
            text = str(cta)
            href = "#"
        if text:
            links.append(f'    <a class="button" href="{escape(href)}">{escape(str(text))}</a>')
    if not links:
        return ""
    return "\n".join(['  <div class="actions">', *links, "  </div>"])


def _first_text(elements: list[dict[str, Any]], tags: set[str]) -> str:
    for element in elements:
        if element.get("tag") in tags and element.get("text"):
            return element["text"]
    return ""


def _section_id(text: str, fallback_index: int) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in text).strip("-")
    slug = "-".join(part for part in slug.split("-") if part)
    return slug[:48] or f"section-{fallback_index}"


def _classify_section(text: str, index: int) -> str:
    lowered = text.lower()
    if index == 0:
        return "hero"
    if any(word in lowered for word in ("price", "pricing", "plan")):
        return "pricing"
    if any(word in lowered for word in ("feature", "benefit", "how it works")):
        return "features"
    if any(word in lowered for word in ("start", "join", "book", "try", "contact", "demo")):
        return "cta"
    return "content"


def _looks_like_cta(text: str) -> bool:
    lowered = text.lower()
    return any(
        phrase in lowered
        for phrase in ("start", "try", "buy", "book", "join", "contact", "demo", "sign up", "get ")
    )


def _improve_headline(headline: str) -> str:
    headline = headline.strip()
    if not headline:
        return "See the value faster"
    return headline if len(headline) > 72 else f"{headline}: clearer value, faster action"


def _parse_multipart_payload(content_type: str, body: bytes) -> dict[str, Any]:
    message = BytesParser(policy=default).parsebytes(
        b"Content-Type: " + content_type.encode("utf-8") + b"\r\n"
        b"MIME-Version: 1.0\r\n\r\n"
        + body
    )
    payload: dict[str, Any] = {}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if not name:
            continue
        filename = part.get_filename()
        content = part.get_payload(decode=True) or b""
        if filename:
            if not filename.lower().endswith((".html", ".htm")):
                raise ValueError("uploaded file must be .html or .htm")
            payload["filename"] = filename
            payload["html"] = content.decode(part.get_content_charset() or "utf-8")
        else:
            payload[name] = content.decode(part.get_content_charset() or "utf-8")
    return payload


def _html_from_payload(payload: dict[str, Any]) -> str:
    html = payload.get("html")
    if isinstance(html, str) and html.strip():
        return html

    html_path = payload.get("html_path")
    if isinstance(html_path, str) and html_path.strip():
        path = Path(html_path).expanduser()
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        if path.suffix.lower() not in {".html", ".htm"}:
            raise ValueError("html_path must point to a .html or .htm file")
        if not path.exists():
            raise ValueError(f"html_path does not exist: {path}")
        return path.read_text(encoding="utf-8")

    if DEFAULT_WEBSITE_HTML.exists():
        return DEFAULT_WEBSITE_HTML.read_text(encoding="utf-8")

    raise ValueError(
        "send an .html file upload, raw html, html_path, or create website/index.html"
    )


def _read_html_or_message(path: Path, title: str) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return (
        f"<!doctype html><meta charset='utf-8'><title>{escape(title)}</title>"
        f"<body style='font-family:system-ui;padding:40px;color:#4a4a4a'>"
        f"<h1>{escape(title)}</h1><p>Missing file: <code>{escape(str(path))}</code></p>"
        f"<p><a href='/'>Back</a> and click <em>Rewrite my page</em>.</p></body>"
    )


def _render_landing_page() -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Auto-AB — Your landing page rewrites itself</title>
  <style>{_landing_css()}</style>
</head>
<body>
  <main>
    <section class="hero">
      <p class="eyebrow">Auto-AB</p>
      <h1>Your landing page rewrites itself.</h1>
      <p class="sub">Auto-AB watches how visitors behave, finds the friction, and ships a better version. Existing tools tell you what happened — Auto-AB decides what to change next.</p>
      <button class="cta" data-run>Rewrite my page</button>
      <p class="hint">Free during beta · runs on the included demo page · ~3 seconds</p>
    </section>

    <section id="demo" class="demo">
      <div class="status" data-status>Click <em>Rewrite my page</em> to run the optimization loop on <code>website/index.html</code>.</div>

      <div class="result" data-result hidden>
        <div class="lift">
          <span class="lift-label">Estimated lift</span>
          <strong class="lift-value" data-lift>—</strong>
          <span class="lift-meta" data-confidence></span>
        </div>
        <p class="summary" data-summary></p>

        <div class="compare">
          <article>
            <header><h3>Your page</h3><a href="/original" target="_blank" rel="noopener">Open ↗</a></header>
            <iframe src="/original" title="Your page"></iframe>
          </article>
          <article>
            <header><h3>AI-rewritten page</h3><a href="/variant-b" target="_blank" rel="noopener">Open ↗</a></header>
            <iframe data-variant-b title="AI-rewritten page"></iframe>
          </article>
        </div>

        <details class="diagnosis">
          <summary>See the diagnosis</summary>
          <ul data-recommendations></ul>
        </details>
      </div>
    </section>

    <section class="how">
      <h2>How it works</h2>
      <ol>
        <li><b>Observe.</b> Heatmaps, clicks, scroll depth, session recordings.</li>
        <li><b>Diagnose.</b> An LLM names the biggest conversion bottleneck.</li>
        <li><b>Generate.</b> A new variant that tests one focused hypothesis.</li>
        <li><b>Predict.</b> Estimated lift before you ship the test.</li>
      </ol>
    </section>

    <section class="quote">
      <blockquote>Existing tools tell you what happened.<br>Auto-AB decides what to change next.</blockquote>
    </section>

    <footer>
      <span>Auto-AB · simulated demo</span>
      <a href="/api">API</a>
      <a href="/website">Demo JSON</a>
    </footer>
  </main>

  <script>
    const $ = (s) => document.querySelector(s);
    const status = document.querySelector('[data-status]');
    const result = document.querySelector('[data-result]');
    const button = document.querySelector('[data-run]');

    async function run() {{
      button.disabled = true;
      status.textContent = 'Analyzing simulated sessions and rewriting the page…';
      try {{
        const r = await fetch('/api/optimize-website');
        const data = await r.json();
        if (data.error) {{
          status.textContent = 'Could not run: ' + data.error;
          button.disabled = false;
          return;
        }}
        render(data);
      }} catch (e) {{
        status.textContent = 'Network error: ' + e.message;
        button.disabled = false;
      }}
    }}

    function render(data) {{
      const ab = data.simulated_ab_result || {{}};
      const lift = ab.predicted_conversion_lift || 0;
      const conf = ab.confidence || 'unknown';
      const analysis = data.llm_analysis || {{}};
      const recs = analysis.recommendations || [];

      document.querySelector('[data-lift]').textContent = (lift >= 0 ? '+' : '') + (lift * 100).toFixed(1) + '%';
      document.querySelector('[data-confidence]').textContent = 'confidence: ' + conf;
      document.querySelector('[data-summary]').textContent = analysis.summary || '';

      const list = document.querySelector('[data-recommendations]');
      list.innerHTML = '';
      recs.forEach((rec) => {{
        const li = document.createElement('li');
        li.textContent = rec;
        list.appendChild(li);
      }});

      const iframe = document.querySelector('[data-variant-b]');
      iframe.src = '/variant-b?ts=' + Date.now();

      status.hidden = true;
      result.hidden = false;
      button.disabled = false;
      button.textContent = 'Run again';
      result.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }}

    button.addEventListener('click', run);
  </script>
</body>
</html>"""


def _landing_css() -> str:
    return """
    *, *::before, *::after { box-sizing: border-box; }
    body { margin: 0; background: #fafaf7; color: #1a1a1a; font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; line-height: 1.5; }
    main { width: min(960px, calc(100% - 40px)); margin: 0 auto; padding: 80px 0 40px; }
    section { margin: 0 0 96px; }
    .eyebrow { margin: 0 0 20px; color: #0f766e; font-weight: 700; text-transform: uppercase; font-size: 0.78rem; letter-spacing: 0.12em; }
    h1 { margin: 0 0 24px; font-size: clamp(2.4rem, 6vw, 4rem); line-height: 1.05; letter-spacing: -0.02em; font-weight: 800; }
    h2 { margin: 0 0 24px; font-size: 1.6rem; letter-spacing: -0.01em; }
    h3 { margin: 0; font-size: 0.95rem; font-weight: 700; }
    .sub { margin: 0 0 32px; max-width: 640px; color: #4a4a4a; font-size: 1.15rem; }
    code { background: #efeee8; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }
    .cta { font: inherit; font-weight: 700; font-size: 1.05rem; padding: 14px 28px; background: #1a1a1a; color: #fff; border: 0; border-radius: 999px; cursor: pointer; }
    .cta:disabled { opacity: 0.5; cursor: wait; }
    .hint { margin: 14px 0 0; color: #888; font-size: 0.9rem; }

    .demo { padding: 32px; background: #fff; border: 1px solid #eee; border-radius: 16px; }
    .status { color: #4a4a4a; }
    .status code { background: #f4f3ec; }
    .lift { display: flex; align-items: baseline; gap: 16px; margin: 0 0 16px; flex-wrap: wrap; }
    .lift-label { color: #888; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700; }
    .lift-value { font-size: 3rem; font-weight: 800; color: #0f766e; letter-spacing: -0.02em; }
    .lift-meta { color: #888; font-size: 0.9rem; }
    .summary { margin: 0 0 28px; color: #333; font-size: 1.05rem; max-width: 640px; }
    .compare { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 0 0 24px; }
    .compare article { background: #fafaf7; border: 1px solid #eee; border-radius: 10px; overflow: hidden; }
    .compare header { display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; border-bottom: 1px solid #eee; }
    .compare a { color: #0f766e; text-decoration: none; font-size: 0.85rem; font-weight: 600; }
    .compare iframe { display: block; width: 100%; height: 480px; border: 0; background: #fff; }
    .diagnosis summary { cursor: pointer; color: #0f766e; font-weight: 600; padding: 8px 0; }
    .diagnosis ul { margin: 12px 0 0; padding-left: 20px; color: #333; }
    .diagnosis li { margin: 6px 0; }

    .how ol { margin: 0; padding: 0; list-style: none; counter-reset: step; display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
    .how li { counter-increment: step; padding: 20px; background: #fff; border: 1px solid #eee; border-radius: 12px; }
    .how li::before { content: counter(step); display: block; color: #0f766e; font-weight: 800; font-size: 0.85rem; margin-bottom: 6px; }

    .quote { text-align: center; padding: 48px 0; }
    .quote blockquote { margin: 0; font-size: 1.6rem; font-weight: 600; line-height: 1.4; letter-spacing: -0.01em; max-width: 700px; margin: 0 auto; }

    footer { display: flex; gap: 20px; align-items: center; padding: 24px 0; border-top: 1px solid #eee; color: #888; font-size: 0.9rem; }
    footer a { color: #4a4a4a; text-decoration: none; }
    footer a:hover { color: #0f766e; }

    @media (max-width: 720px) {
      main { padding-top: 48px; }
      section { margin-bottom: 64px; }
      .compare, .how ol { grid-template-columns: 1fr; }
      .compare iframe { height: 360px; }
    }
    """


class DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlparse(self.path).path
        routes = {
            "/": self._interface,
            "/api": self._index,
            "/original": lambda: _read_html_or_message(DEFAULT_WEBSITE_HTML, "Original not found"),
            "/variant-b": lambda: _read_html_or_message(VARIANT_B_HTML, "Run optimization first"),
            "/website": lambda: DEMO_WEBSITE,
            "/simulate/user-data": lambda: SIMULATED_USER_DATA,
            "/simulate/session-recording": lambda: FAKE_SESSION_RECORDING,
            "/final-result": build_final_result,
            "/api/optimize-website": optimize_default_website,
        }
        handler = routes.get(path)
        if handler is None:
            self._send_json({"error": "not_found", "available_routes": sorted(routes)})
            return
        result = handler()
        if isinstance(result, str):
            self._send_html(result)
            return
        self._send_json(result)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def _cors_headers(self) -> None:
        self.send_header("access-control-allow-origin", "*")
        self.send_header("access-control-allow-methods", "GET, POST, OPTIONS")
        self.send_header("access-control-allow-headers", "content-type")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/analyze-url":
            payload = self._read_json()
            url = (payload.get("url") or "").strip()
            if not url:
                self._send_json({"error": "url required"}, status=400)
                return
            demo_html = _demo_target_html_for_url(url)
            try:
                html = demo_html or _fetch_url_html(url)
            except Exception as error:
                if DEFAULT_WEBSITE_HTML.exists():
                    html = DEFAULT_WEBSITE_HTML.read_text(encoding="utf-8")
                else:
                    self._send_json({"error": f"could not fetch url: {error}"}, status=502)
                    return
            page_context = payload.get("page_context") if isinstance(payload.get("page_context"), dict) else None
            if page_context is None and demo_html:
                page_context = {"sourceFile": str(DEFAULT_WEBSITE_HTML)}
            result = optimize_html_document(
                html=html,
                target_customer=payload.get("target_customer", TARGET_CUSTOMER),
                page_context=page_context,
            )
            self._send_json(_adapt_for_frontend(result, url, payload.get("analytics_source", "simulated")))
            return
        if path == "/optimize-html":
            payload = self._read_payload()
            try:
                html = _html_from_payload(payload)
            except ValueError as error:
                self._send_json({"error": str(error)}, status=400)
                return
            self._send_json(
                _optimize_payload_and_write_files(
                    html=html,
                    target_customer=payload.get("target_customer", TARGET_CUSTOMER),
                    user_data=payload.get("simulated_data"),
                    session_recording=payload.get("session_recording"),
                    page_context=payload.get("page_context") if isinstance(payload.get("page_context"), dict) else None,
                )
            )
            return

        payload = self._read_json()
        if path == "/analyze":
            self._send_json(
                analyze_website(
                    payload.get("website_json", DEMO_WEBSITE),
                    payload.get("simulated_data", SIMULATED_USER_DATA),
                    payload.get("target_customer", TARGET_CUSTOMER),
                    payload.get("session_recording", FAKE_SESSION_RECORDING),
                )
            )
            return
        if path == "/variant":
            analysis = payload.get("analysis") or analyze_website(
                payload.get("website_json", DEMO_WEBSITE),
                payload.get("simulated_data", SIMULATED_USER_DATA),
                payload.get("target_customer", TARGET_CUSTOMER),
                payload.get("session_recording", FAKE_SESSION_RECORDING),
            )
            self._send_json(generate_improved_variant(payload.get("website_json", DEMO_WEBSITE), analysis))
            return
        if path == "/ab-result":
            analysis = payload.get("analysis") or analyze_website(
                payload.get("variant_a", DEMO_WEBSITE),
                payload.get("simulated_data", SIMULATED_USER_DATA),
                payload.get("target_customer", TARGET_CUSTOMER),
                payload.get("session_recording", FAKE_SESSION_RECORDING),
            )
            variant_b = payload.get("variant_b") or generate_improved_variant(
                payload.get("variant_a", DEMO_WEBSITE), analysis
            )
            self._send_json(simulate_ab_result(payload.get("variant_a", DEMO_WEBSITE), variant_b, analysis))
            return
        self._send_json({"error": "not_found"}, status=404)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _index(self) -> dict[str, Any]:
        return {
            "name": "Auto AB demo backend",
            "routes": {
                "GET /": "Landing page with inline demo.",
                "GET /api": "API route index.",
                "GET /original": "Serve website/index.html (the seed page).",
                "GET /variant-b": "Serve generated website/variant-b.html.",
                "GET /website": "Demo website JSON.",
                "GET /simulate/user-data": "Heatmap points, scroll depth, clicks.",
                "GET /simulate/session-recording": "Timestamped cursor, click, scroll events.",
                "GET /api/optimize-website": "Run optimization on website/index.html; return JSON.",
                "GET /final-result": "Run the full demo loop and return all artifacts.",
                "POST /analyze": "Analyze a website_json for friction.",
                "POST /analyze-url": "Fetch a public URL, run the loop, return frontend-shaped result.",
                "POST /optimize-html": "Optimize an HTML page (file/string/path).",
                "POST /variant": "Generate improved website JSON.",
                "POST /ab-result": "Predict A vs B conversion lift.",
            },
        }

    def _interface(self) -> str:
        return _render_landing_page()

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("content-length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _read_payload(self) -> dict[str, Any]:
        length = int(self.headers.get("content-length", "0"))
        if length == 0:
            return {}
        body = self.rfile.read(length)
        content_type = self.headers.get("content-type", "")
        if content_type.startswith("multipart/form-data"):
            return _parse_multipart_payload(content_type, body)
        if content_type.startswith("text/html"):
            return {"html": body.decode("utf-8")}
        return json.loads(body.decode("utf-8"))

    def _send_html(self, body: str, status: int = 200) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("content-length", str(len(encoded)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(encoded)

    def _send_json(self, body: Any, status: int = 200) -> None:
        encoded = json.dumps(body, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(encoded)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(encoded)


def _click_counts_by_target(clicks: list[dict[str, Any]]) -> dict[tuple[str, str], int]:
    return {
        (click.get("section", ""), click.get("target", "")): int(click.get("count", 0))
        for click in clicks
    }


def _confidence_from_signal_count(signal_count: int) -> str:
    score = 1 - math.exp(-signal_count / 3)
    if score >= 0.7:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


INTERFACE_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Auto AB Demo</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #1f2933;
      --muted: #657083;
      --line: #d8dee8;
      --accent: #0f766e;
      --accent-dark: #115e59;
      --good: #15803d;
      --warn: #b45309;
      --bad: #b91c1c;
      --shadow: 0 16px 40px rgba(31, 41, 51, 0.08);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }

    button,
    textarea {
      font: inherit;
    }

    .shell {
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0 40px;
    }

    header {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 18px;
      align-items: end;
      padding: 14px 0 24px;
    }

    h1,
    h2,
    h3,
    p {
      margin: 0;
    }

    h1 {
      font-size: clamp(2rem, 5vw, 4.25rem);
      line-height: 0.95;
      letter-spacing: 0;
      max-width: 720px;
    }

    .subtitle {
      max-width: 660px;
      margin-top: 14px;
      color: var(--muted);
      font-size: 1rem;
    }

    .status {
      min-width: 168px;
      padding: 10px 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      color: var(--muted);
      text-align: center;
      box-shadow: var(--shadow);
    }

    .controls {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: stretch;
      margin-bottom: 18px;
    }

    textarea {
      min-height: 72px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      color: var(--text);
      padding: 12px 14px;
      outline: none;
      box-shadow: var(--shadow);
    }

    textarea:focus {
      border-color: var(--accent);
    }

    button {
      border: 0;
      border-radius: 8px;
      background: var(--accent);
      color: white;
      padding: 0 22px;
      min-height: 52px;
      cursor: pointer;
      font-weight: 700;
      box-shadow: var(--shadow);
    }

    button:hover {
      background: var(--accent-dark);
    }

    button:disabled {
      cursor: wait;
      opacity: 0.68;
    }

    .metrics {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin: 18px 0;
    }

    .metric,
    .panel,
    .page-preview,
    .friction-item {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      box-shadow: var(--shadow);
    }

    .metric {
      padding: 14px;
    }

    .metric span {
      display: block;
      color: var(--muted);
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .metric strong {
      display: block;
      margin-top: 4px;
      font-size: clamp(1.35rem, 3vw, 2.2rem);
      line-height: 1.05;
    }

    .grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 16px;
      align-items: start;
    }

    .panel {
      padding: 18px;
      min-width: 0;
    }

    .panel h2 {
      font-size: 1.05rem;
      margin-bottom: 10px;
    }

    .summary {
      color: var(--muted);
      margin-bottom: 14px;
    }

    .friction-list {
      display: grid;
      gap: 10px;
    }

    .friction-item {
      padding: 12px;
      box-shadow: none;
    }

    .tag {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 2px 8px;
      border-radius: 999px;
      background: #eef2f7;
      color: var(--muted);
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    .tag.high {
      background: #fee2e2;
      color: var(--bad);
    }

    .tag.medium {
      background: #ffedd5;
      color: var(--warn);
    }

    .tag.low {
      background: #dcfce7;
      color: var(--good);
    }

    .friction-item h3 {
      margin: 8px 0 4px;
      font-size: 0.96rem;
    }

    .friction-item p {
      color: var(--muted);
      font-size: 0.92rem;
    }

    .versions {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 16px;
      margin-top: 16px;
    }

    .page-preview {
      min-width: 0;
      overflow: hidden;
    }

    .preview-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
    }

    .preview-head h2 {
      font-size: 1rem;
    }

    .section {
      padding: 16px 14px;
      border-bottom: 1px solid var(--line);
    }

    .section:last-child {
      border-bottom: 0;
    }

    .section h3 {
      font-size: 1.08rem;
      line-height: 1.2;
      margin-bottom: 8px;
    }

    .section p,
    .section li {
      color: var(--muted);
      font-size: 0.92rem;
    }

    .section ul {
      margin: 8px 0 0;
      padding-left: 18px;
    }

    .cta-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }

    .pill {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 5px 9px;
      color: var(--text);
      font-size: 0.82rem;
      font-weight: 700;
    }

    .raw {
      margin-top: 16px;
    }

    pre {
      overflow: auto;
      max-height: 420px;
      margin: 0;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #111827;
      color: #d1d5db;
      font-size: 0.82rem;
      line-height: 1.45;
    }

    @media (max-width: 860px) {
      header,
      .controls,
      .grid,
      .versions {
        grid-template-columns: 1fr;
      }

      .status {
        text-align: left;
      }

      button {
        width: 100%;
      }

      .metrics {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 520px) {
      .shell {
        width: min(100% - 20px, 1180px);
        padding-top: 14px;
      }

      .metrics {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <header>
      <div>
        <h1>Auto AB Demo</h1>
        <p class="subtitle">Run the backend loop, inspect the friction analysis, compare Variant A with Variant B, and review the predicted A/B result.</p>
      </div>
      <div class="status" id="status">Ready</div>
    </header>

    <section class="controls" aria-label="Demo controls">
      <textarea id="targetCustomer" aria-label="Target customer"></textarea>
      <button id="runButton" type="button">Run demo</button>
    </section>

    <section class="metrics" aria-label="A/B result metrics">
      <div class="metric"><span>Lift</span><strong id="lift">-</strong></div>
      <div class="metric"><span>Confidence</span><strong id="confidence">-</strong></div>
      <div class="metric"><span>Variant A CR</span><strong id="rateA">-</strong></div>
      <div class="metric"><span>Variant B CR</span><strong id="rateB">-</strong></div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Analysis</h2>
        <p class="summary" id="summary">Run the demo to generate analysis.</p>
        <div class="friction-list" id="frictionList"></div>
      </div>
      <div class="panel">
        <h2>Recommendations</h2>
        <div class="friction-list" id="recommendations"></div>
      </div>
    </section>

    <section class="versions" aria-label="Variant comparison">
      <article class="page-preview">
        <div class="preview-head">
          <h2>Variant A</h2>
          <span class="tag">Current</span>
        </div>
        <div id="variantA"></div>
      </article>
      <article class="page-preview">
        <div class="preview-head">
          <h2>Variant B</h2>
          <span class="tag low">Generated</span>
        </div>
        <div id="variantB"></div>
      </article>
    </section>

    <section class="raw">
      <pre id="rawJson">{}</pre>
    </section>
  </main>

  <script>
    const defaultTarget = "small businesses, indie founders, agencies, and e-commerce brands that see drop-offs but do not know what to change";
    const targetCustomer = document.querySelector("#targetCustomer");
    const runButton = document.querySelector("#runButton");
    const statusEl = document.querySelector("#status");
    targetCustomer.value = defaultTarget;

    async function getJson(url) {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`${url} returned ${response.status}`);
      return response.json();
    }

    async function postJson(url, payload) {
      const response = await fetch(url, {
        method: "POST",
        headers: {"content-type": "application/json"},
        body: JSON.stringify(payload)
      });
      if (!response.ok) throw new Error(`${url} returned ${response.status}`);
      return response.json();
    }

    function formatPercent(value) {
      if (typeof value !== "number") return "-";
      return `${Math.round(value * 1000) / 10}%`;
    }

    function setStatus(text) {
      statusEl.textContent = text;
    }

    function renderFriction(points) {
      const list = document.querySelector("#frictionList");
      list.innerHTML = "";
      if (!points.length) {
        list.innerHTML = '<p class="summary">No friction points returned.</p>';
        return;
      }
      points.forEach((point) => {
        const item = document.createElement("article");
        item.className = "friction-item";
        item.innerHTML = `
          <span class="tag ${point.severity || ""}">${point.severity || "signal"}</span>
          <h3>${point.section || "Section"}</h3>
          <p>${point.evidence || ""}</p>
          <p><strong>Change:</strong> ${point.recommendation || ""}</p>
        `;
        list.appendChild(item);
      });
    }

    function renderRecommendations(items) {
      const list = document.querySelector("#recommendations");
      list.innerHTML = "";
      if (!items.length) {
        list.innerHTML = '<p class="summary">No recommendations returned.</p>';
        return;
      }
      items.forEach((text, index) => {
        const item = document.createElement("article");
        item.className = "friction-item";
        item.innerHTML = `<span class="tag">${index + 1}</span><p>${text}</p>`;
        list.appendChild(item);
      });
    }

    function renderSections(rootId, website) {
      const root = document.querySelector(rootId);
      root.innerHTML = "";
      (website.sections || []).forEach((section) => {
        const block = document.createElement("section");
        block.className = "section";
        const items = Array.isArray(section.items)
          ? `<ul>${section.items.map((item) => `<li>${item}</li>`).join("")}</ul>`
          : "";
        const plans = Array.isArray(section.plans)
          ? `<ul>${section.plans.map((plan) => `<li><strong>${plan.name}</strong> ${plan.price}: ${plan.description}</li>`).join("")}</ul>`
          : "";
        const ctas = [section.primary_cta, section.secondary_cta].filter(Boolean)
          .map((cta) => `<span class="pill">${cta}</span>`).join("");
        block.innerHTML = `
          <h3>${section.headline || section.id}</h3>
          ${section.subheadline ? `<p>${section.subheadline}</p>` : ""}
          ${section.body ? `<p>${section.body}</p>` : ""}
          ${section.proof ? `<p>${section.proof}</p>` : ""}
          ${items}
          ${plans}
          ${ctas ? `<div class="cta-row">${ctas}</div>` : ""}
          ${section.change_reason ? `<p><strong>Why changed:</strong> ${section.change_reason}</p>` : ""}
        `;
        root.appendChild(block);
      });
    }

    async function runDemo() {
      runButton.disabled = true;
      setStatus("Loading data");
      try {
        const [website, userData, sessionRecording] = await Promise.all([
          getJson("/website"),
          getJson("/simulate/user-data"),
          getJson("/simulate/session-recording")
        ]);
        const basePayload = {
          website_json: website,
          simulated_data: userData,
          session_recording: sessionRecording,
          target_customer: targetCustomer.value.trim() || defaultTarget
        };

        setStatus("Analyzing");
        const analysis = await postJson("/analyze", basePayload);
        setStatus("Generating B");
        const variantB = await postJson("/variant", {...basePayload, analysis});
        setStatus("Simulating");
        const abResult = await postJson("/ab-result", {
          variant_a: website,
          variant_b: variantB,
          analysis,
          simulated_data: userData,
          session_recording: sessionRecording,
          target_customer: basePayload.target_customer
        });

        document.querySelector("#lift").textContent = formatPercent(abResult.predicted_conversion_lift);
        document.querySelector("#confidence").textContent = abResult.confidence || "-";
        document.querySelector("#rateA").textContent = formatPercent(abResult.variant_a?.predicted_conversion_rate);
        document.querySelector("#rateB").textContent = formatPercent(abResult.variant_b?.predicted_conversion_rate);
        document.querySelector("#summary").textContent = analysis.summary || "No summary returned.";
        renderFriction(analysis.friction_points || []);
        renderRecommendations(analysis.recommendations || []);
        renderSections("#variantA", website);
        renderSections("#variantB", variantB);
        document.querySelector("#rawJson").textContent = JSON.stringify({
          demo_website_json: website,
          simulated_user_data: userData,
          fake_session_recording: sessionRecording,
          llm_analysis: analysis,
          improved_variant_json: variantB,
          simulated_ab_result: abResult
        }, null, 2);
        setStatus(`Provider: ${analysis.provider || "unknown"}`);
      } catch (error) {
        setStatus("Error");
        document.querySelector("#summary").textContent = error.message;
      } finally {
        runButton.disabled = false;
      }
    }

    runButton.addEventListener("click", runDemo);
    runDemo();
  </script>
</body>
</html>
"""


def main() -> None:
    preferred_port = int(os.getenv("PORT", "8000"))
    ports = [preferred_port, *range(8001, 8010)]
    server = None
    port = preferred_port
    for candidate in ports:
        try:
            server = ThreadingHTTPServer(("127.0.0.1", candidate), DemoHandler)
            port = candidate
            break
        except OSError:
            continue
    if server is None:
        raise RuntimeError("No available local port found from 8000 through 8009.")

    print(f"Auto AB demo backend running at http://127.0.0.1:{port}")
    print(f"Open http://127.0.0.1:{port} for the browser interface.")
    print(f"Open http://127.0.0.1:{port}/final-result for the complete JSON output.")
    server.serve_forever()


if __name__ == "__main__":
    main()
