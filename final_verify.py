import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse


DATA = Path("data")
RESULTS = DATA / "results.json"
VERIFY = DATA / "verification.csv"
ACCURACY = DATA / "accuracy.json"
QA_REPORT = DATA / "qa_report.json"

# Validated Composio coverage.
LOCKED = {
    "existing_toolkit": 57,
    "toolkit_gap": 42,
    "unresolved": 1,
}


# ============================================================
# HELPERS
# ============================================================

def load_apps():
    if not RESULTS.exists():
        raise SystemExit(
            "ERROR: data/results.json not found. "
            "Run this script from E:\\Composio."
        )

    data = json.loads(RESULTS.read_text(encoding="utf-8"))

    apps = data.get("apps")

    if not isinstance(apps, list):
        raise SystemExit(
            "ERROR: results.json must contain an 'apps' list."
        )

    return apps


def txt(value):
    if value is None:
        return "unknown"

    if isinstance(value, list):
        return " | ".join(map(str, value)) if value else "unknown"

    return str(value)


def confidence_bucket(app):
    try:
        confidence = float(app.get("confidence", 0) or 0)
    except (TypeError, ValueError):
        confidence = 0

    if confidence >= 0.8:
        return "high"

    if confidence >= 0.5:
        return "medium"

    return "low"


def valid_url(url):
    try:
        parsed = urlparse(str(url or ""))

        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.netloc)
        )

    except Exception:
        return False


# ============================================================
# STRATIFIED SAMPLE
# ============================================================

def choose_sample(apps, sample_size):
    rng = random.Random(42)

    pool = apps[:]
    rng.shuffle(pool)

    selected = []
    selected_names = set()

    by_category = defaultdict(list)

    for app in pool:
        category = app.get("category", "unknown")
        by_category[category].append(app)

    # First ensure category diversity.
    for category in by_category:

        if len(selected) >= sample_size:
            break

        candidate = min(
            by_category[category],
            key=lambda app: (
                {
                    "low": 0,
                    "medium": 1,
                    "high": 2
                }[confidence_bucket(app)],
                app.get("composio_status", "")
            )
        )

        selected.append(candidate)
        selected_names.add(candidate.get("app"))

    # Fill remaining positions while maximizing diversity.
    while len(selected) < min(sample_size, len(apps)):

        remaining = [
            app
            for app in pool
            if app.get("app") not in selected_names
        ]

        confidence_counts = Counter(
            confidence_bucket(app)
            for app in selected
        )

        composio_counts = Counter(
            app.get("composio_status", "unknown")
            for app in selected
        )

        buildability_counts = Counter(
            app.get("buildability", "unknown")
            for app in selected
        )

        def score(app):

            score_value = (
                1 / (
                    1 +
                    confidence_counts[
                        confidence_bucket(app)
                    ]
                )
                +
                1 / (
                    1 +
                    composio_counts[
                        app.get(
                            "composio_status",
                            "unknown"
                        )
                    ]
                )
                +
                1 / (
                    1 +
                    buildability_counts[
                        app.get(
                            "buildability",
                            "unknown"
                        )
                    ]
                )
            )

            # Slight preference for uncertain records.
            if confidence_bucket(app) != "high":
                score_value += 0.25

            return score_value

        candidate = max(
            remaining,
            key=score
        )

        selected.append(candidate)
        selected_names.add(
            candidate.get("app")
        )

    return selected


# ============================================================
# CREATE HUMAN VERIFICATION SAMPLE
# ============================================================

def create_sample(sample_size):

    apps = load_apps()

    sample_size = max(
        1,
        min(sample_size, len(apps))
    )

    chosen = choose_sample(
        apps,
        sample_size
    )

    DATA.mkdir(
        exist_ok=True
    )

    fields = [
        "app",
        "category",
        "confidence",
        "composio_status",

        "first_pass_auth",
        "verified_auth",
        "auth_correct",

        "first_pass_access",
        "verified_access",
        "access_correct",

        "first_pass_api",
        "verified_api",
        "api_correct",

        "first_pass_mcp",
        "verified_mcp",
        "mcp_correct",

        "first_pass_buildability",
        "verified_buildability",
        "buildability_correct",

        "first_pass_composio",
        "verified_composio",
        "composio_correct",

        "correction_reason",
        "verification_url",
        "verification_notes"
    ]

    with VERIFY.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()

        for app in chosen:

            writer.writerow({

                "app":
                    app.get("app", ""),

                "category":
                    app.get("category", ""),

                "confidence":
                    app.get("confidence", ""),

                "composio_status":
                    app.get(
                        "composio_status",
                        ""
                    ),

                "first_pass_auth":
                    txt(
                        app.get(
                            "auth_methods"
                        )
                    ),

                "first_pass_access":
                    txt(
                        app.get(
                            "access"
                        )
                    ),

                "first_pass_api":
                    (
                        f"{txt(app.get('api_type'))}"
                        " / "
                        f"{txt(app.get('api_breadth'))}"
                    ),

                "first_pass_mcp":
                    txt(
                        app.get(
                            "native_mcp_status"
                        )
                    ),

                "first_pass_buildability":
                    txt(
                        app.get(
                            "buildability"
                        )
                    ),

                "first_pass_composio":
                    txt(
                        app.get(
                            "composio_status"
                        )
                    )
            })

    print("=" * 70)
    print("VERIFICATION SAMPLE CREATED")
    print("=" * 70)

    print(
        f"Created {VERIFY} "
        f"with {len(chosen)} apps."
    )

    print(
        "\nFill verified_* columns manually."
    )

    print(
        "Use yes/no in each *_correct column."
    )

    print(
        "Use official documentation whenever possible."
    )


# ============================================================
# ACCURACY
# ============================================================

def parse_bool(value):

    value = str(
        value or ""
    ).strip().lower()

    if value in {
        "yes",
        "y",
        "true",
        "1",
        "correct",
        "pass"
    }:
        return True

    if value in {
        "no",
        "n",
        "false",
        "0",
        "incorrect",
        "fail"
    }:
        return False

    return None


def calculate_accuracy():

    if not VERIFY.exists():

        raise SystemExit(
            "ERROR: Run "
            "`python final_verify.py sample --sample 20` "
            "first."
        )

    with VERIFY.open(
        "r",
        encoding="utf-8-sig"
    ) as file:

        rows = list(
            csv.DictReader(file)
        )

    mapping = {

        "auth":
            "auth_correct",

        "access":
            "access_correct",

        "api":
            "api_correct",

        "mcp":
            "mcp_correct",

        "buildability":
            "buildability_correct",

        "composio":
            "composio_correct"
    }

    output = {}

    total_correct = 0
    total_checked = 0

    for label, field in mapping.items():

        values = [
            parse_bool(
                row.get(field)
            )
            for row in rows
        ]

        values = [
            value
            for value in values
            if value is not None
        ]

        correct = sum(values)
        checked = len(values)

        output[label] = {

            "correct":
                correct,

            "checked":
                checked,

            "accuracy":
                (
                    round(
                        correct / checked,
                        4
                    )
                    if checked
                    else None
                )
        }

        total_correct += correct
        total_checked += checked

    output["overall"] = {

        "correct":
            total_correct,

        "checked":
            total_checked,

        "accuracy":
            (
                round(
                    total_correct /
                    total_checked,
                    4
                )
                if total_checked
                else None
            )
    }

    output["sample_rows"] = len(rows)

    ACCURACY.write_text(
        json.dumps(
            output,
            indent=2
        ),
        encoding="utf-8"
    )

    print(
        json.dumps(
            output,
            indent=2
        )
    )

    if total_checked == 0:

        print(
            "\nManual verification pending."
        )

        print(
            "Do NOT show an accuracy "
            "percentage in the HTML yet."
        )


# ============================================================
# FINAL QA
# ============================================================

def run_qa():

    apps = load_apps()

    errors = []
    warnings = []

    names = [
        app.get("app")
        for app in apps
    ]

    # --------------------------------------------------------
    # HARD FAILURE 1: dataset size
    # --------------------------------------------------------

    if len(apps) != 100:

        errors.append(
            f"Expected 100 apps; "
            f"found {len(apps)}."
        )

    # --------------------------------------------------------
    # HARD FAILURE 2: duplicate apps
    # --------------------------------------------------------

    if len(set(names)) != len(names):

        duplicates = [
            name
            for name, count
            in Counter(names).items()
            if count > 1
        ]

        errors.append(
            f"Duplicate apps detected: "
            f"{duplicates}"
        )

    # --------------------------------------------------------
    # HARD FAILURE 3: validated Composio invariant
    # --------------------------------------------------------

    composio_counts = Counter(

        app.get(
            "composio_status",
            "unknown"
        )

        for app in apps
    )

    for status, expected in LOCKED.items():

        actual = composio_counts.get(
            status,
            0
        )

        if actual != expected:

            errors.append(

                "Composio invariant failed: "
                f"{status}={actual}, "
                f"expected {expected}."
            )

    # --------------------------------------------------------
    # PER APP CHECKS
    # --------------------------------------------------------

    for app in apps:

        name = app.get(
            "app",
            "UNKNOWN"
        )

        status = app.get(
            "composio_status"
        )

        slug = app.get(
            "composio_toolkit_slug"
        )

        toolkit_url = app.get(
            "composio_toolkit_url"
        )

        # ----------------------------------------------------
        # HARD: existing toolkit must have slug
        # ----------------------------------------------------

        if status == "existing_toolkit":

            if not slug:

                errors.append(
                    f"{name}: "
                    "existing toolkit missing slug."
                )

            if not valid_url(
                toolkit_url
            ):

                warnings.append(
                    f"{name}: "
                    "existing toolkit has "
                    "missing/invalid toolkit URL."
                )

        # ----------------------------------------------------
        # HARD: gap shouldn't have toolkit slug
        # ----------------------------------------------------

        elif (
            status == "toolkit_gap"
            and slug
        ):

            errors.append(
                f"{name}: "
                "toolkit gap incorrectly "
                "contains toolkit slug."
            )

        # ----------------------------------------------------
        # HARD: confidence must be valid
        # ----------------------------------------------------

        try:

            confidence = float(
                app.get(
                    "confidence",
                    0
                ) or 0
            )

            if not 0 <= confidence <= 1:

                errors.append(
                    f"{name}: "
                    "confidence outside 0..1."
                )

        except (
            TypeError,
            ValueError
        ):

            errors.append(
                f"{name}: "
                "invalid confidence value."
            )

            confidence = 0

        # ----------------------------------------------------
        # HARD: valid MCP enum
        # ----------------------------------------------------

        mcp_status = app.get(
            "native_mcp_status",
            "unknown"
        )

        allowed_mcp = {
            "official",
            "community",
            "none",
            "unknown",
            None
        }

        if mcp_status not in allowed_mcp:

            errors.append(
                f"{name}: "
                f"invalid native_mcp_status "
                f"'{mcp_status}'."
            )

        # ----------------------------------------------------
        # HARD: valid buildability enum
        # ----------------------------------------------------

        buildability = app.get(
            "buildability",
            "unknown"
        )

        allowed_buildability = {
            "ready",
            "ready_with_constraints",
            "blocked",
            "unknown",
            None
        }

        if (
            buildability
            not in allowed_buildability
        ):

            errors.append(
                f"{name}: "
                f"invalid buildability "
                f"'{buildability}'."
            )

        # ----------------------------------------------------
        # Collect valid evidence URLs
        # ----------------------------------------------------

        evidence = []

        for item in (
            app.get(
                "evidence"
            ) or []
        ):

            if not isinstance(
                item,
                dict
            ):
                continue

            if valid_url(
                item.get("url")
            ):

                evidence.append(
                    item
                )

        # ----------------------------------------------------
        # SOFT WARNING:
        # High confidence but missing evidence
        # ----------------------------------------------------

        if (
            confidence >= 0.8
            and not evidence
        ):

            warnings.append(

                f"{name}: "
                "high confidence without "
                "a valid evidence URL."
            )

        # ----------------------------------------------------
        # SOFT WARNING:
        # Official MCP without stored official MCP evidence
        # ----------------------------------------------------

        if mcp_status == "official":

            supported = False

            for item in evidence:

                blob = (
                    str(
                        item.get(
                            "claim",
                            ""
                        )
                    )
                    + " "
                    + str(
                        item.get(
                            "supporting_text",
                            ""
                        )
                    )
                    + " "
                    + str(
                        item.get(
                            "source_title",
                            ""
                        )
                    )
                ).lower()

                quality = str(
                    item.get(
                        "source_quality",
                        ""
                    )
                ).lower()

                official_sources = {

                    "official_docs",
                    "official_github",
                    "official",
                    "vendor_docs",
                    "vendor_github"
                }

                if (
                    "mcp" in blob
                    and
                    quality
                    in official_sources
                ):

                    supported = True
                    break

            if not supported:

                warnings.append(

                    f"{name}: "
                    "official native MCP lacks "
                    "stored official MCP evidence."
                )

    # --------------------------------------------------------
    # ACCURACY SANITY CHECK
    # --------------------------------------------------------

    if ACCURACY.exists():

        try:

            accuracy_data = json.loads(
                ACCURACY.read_text(
                    encoding="utf-8"
                )
            )

            overall = (
                accuracy_data.get(
                    "overall",
                    {}
                )
            )

            checked = overall.get(
                "checked",
                0
            )

            accuracy_value = overall.get(
                "accuracy"
            )

            if (
                checked == 0
                and
                accuracy_value is not None
            ):

                errors.append(

                    "accuracy.json contains "
                    "an accuracy percentage "
                    "despite zero manually "
                    "checked fields."
                )

        except Exception as exc:

            errors.append(
                "Invalid accuracy.json: "
                f"{exc}"
            )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    report = {

        "pass":
            not errors,

        "apps":
            len(apps),

        "unique_apps":
            len(set(names)),

        "composio":
            dict(
                composio_counts
            ),

        "errors":
            errors,

        "warnings":
            warnings
    }

    QA_REPORT.write_text(

        json.dumps(
            report,
            indent=2
        ),

        encoding="utf-8"
    )

    # --------------------------------------------------------
    # TERMINAL OUTPUT
    # --------------------------------------------------------

    print(
        "=" * 70
    )

    print(
        "FINAL QA"
    )

    print(
        "=" * 70
    )

    print(
        f"Apps: {len(apps)} "
        f"| Unique: {len(set(names))}"
    )

    print(
        "Composio:",
        dict(
            composio_counts
        )
    )

    print(
        f"Errors: {len(errors)} "
        f"| Warnings: {len(warnings)}"
    )

    if errors:

        print(
            "\nHARD ERRORS:"
        )

        for error in errors:

            print(
                "ERROR:",
                error
            )

    if warnings:

        print(
            "\nSOFT WARNINGS:"
        )

        for warning in warnings:

            print(
                "WARNING:",
                warning
            )

    print()

    if errors:

        print(
            "QA: FAIL"
        )

    elif warnings:

        print(
            "QA: PASS WITH WARNINGS"
        )

    else:

        print(
            "QA: PASS"
        )

    print(
        "Report:",
        QA_REPORT
    )

    return (
        0
        if not errors
        else 1
    )


# ============================================================
# CLI
# ============================================================

def main():

    parser = argparse.ArgumentParser(

        description=(
            "Final verification and QA "
            "for the Composio assignment."
        )
    )

    commands = parser.add_subparsers(
        dest="command",
        required=True
    )

    sample_parser = commands.add_parser(
        "sample"
    )

    sample_parser.add_argument(
        "--sample",
        type=int,
        default=20
    )

    commands.add_parser(
        "accuracy"
    )

    commands.add_parser(
        "qa"
    )

    args = parser.parse_args()

    if args.command == "sample":

        create_sample(
            args.sample
        )

        return 0

    if args.command == "accuracy":

        calculate_accuracy()

        return 0

    if args.command == "qa":

        return run_qa()

    return 1


if __name__ == "__main__":

    raise SystemExit(
        main()
    )