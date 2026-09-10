import json
import sys
from collections import Counter

REPORT = "license-report.json"

# Licenses that are currently approved for automatic use
APPROVED_LICENSES = {
    "MIT",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "PSF-2.0",
}

# Licenses that require legal/security review
REVIEW_LICENSES = {
    "LGPL-3.0-only",
    "LGPL-3.0-or-later",
    "MPL-2.0",
    "BlueOak-1.0.0",
    "CC0-1.0",
    "CC-BY-SA-4.0",
    "BSL-1.0",
    "Unlicense",
    "Python-2.0",
    "BSD",
    "Dual License",
}


def normalize_license(value):
    if not value:
        return None

    value = value.strip()

    # Obvious invalid license data
    if value.lower().startswith("sha256:"):
        return "INVALID_LICENSE_DATA"

    # Normalize common variations
    aliases = {
        "MIT License": "MIT",
        "Apache 2": "Apache-2.0",
        "Apache 2.0": "Apache-2.0",
        "Apache License Version 2.0": "Apache-2.0",
        "ISC License": "ISC",
        "PSF": "PSF-2.0",
        "3-Clause BSD License": "BSD-3-Clause",
    }

    if value in aliases:
        return aliases[value]

    return value


def evaluate_license(value):
    """
    Returns:
        APPROVED
        REVIEW_REQUIRED
        LICENSE_NOT_DETECTED
        INVALID_LICENSE_DATA
    """

    if not value:
        return "LICENSE_NOT_DETECTED"

    value = normalize_license(value)

    if value == "INVALID_LICENSE_DATA":
        return "INVALID_LICENSE_DATA"

    # Handle OR expressions.
    if " OR " in value:
        options = [x.strip() for x in value.split(" OR ")]

        results = [evaluate_license(option) for option in options]

        if all(result == "APPROVED" for result in results):
            return "APPROVED"

        if any(result == "REVIEW_REQUIRED" for result in results):
            return "REVIEW_REQUIRED"

        if any(result == "LICENSE_NOT_DETECTED" for result in results):
            return "REVIEW_REQUIRED"

        return "REVIEW_REQUIRED"

    if value in APPROVED_LICENSES:
        return "APPROVED"

    if value in REVIEW_LICENSES:
        return "REVIEW_REQUIRED"

    # Unknown license → manual review
    return "REVIEW_REQUIRED"


def main():
    try:
        with open(REPORT, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: {REPORT} not found")
        sys.exit(1)

    artifacts = data.get("artifacts", [])

    results = []
    summary = Counter()

    for artifact in artifacts:
        package = artifact.get("name", "UNKNOWN")
        version = artifact.get("version", "UNKNOWN")
        artifact_type = artifact.get("type", "UNKNOWN")

        licenses = artifact.get("licenses") or []

        if not licenses:
            status = "LICENSE_NOT_DETECTED"

            results.append({
                "package": package,
                "version": version,
                "type": artifact_type,
                "license": None,
                "status": status,
            })

            summary[status] += 1
            continue

        for license_info in licenses:

            if isinstance(license_info, dict):
                license_value = (
                    license_info.get("spdxExpression")
                    or license_info.get("value")
                    or ""
                )
            else:
                license_value = str(license_info)

            status = evaluate_license(license_value)

            results.append({
                "package": package,
                "version": version,
                "type": artifact_type,
                "license": license_value,
                "status": status,
            })

            summary[status] += 1

    output_file = "license-policy-report.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "summary": dict(summary),
                "results": results,
            },
            f,
            indent=2,
        )

    print("")
    print("==============================================")
    print("       OpenSandbox License Policy")
    print("==============================================")
    print(f"Total license records : {len(results)}")
    print("----------------------------------------------")
    print(f"APPROVED              : {summary['APPROVED']}")
    print(f"REVIEW_REQUIRED       : {summary['REVIEW_REQUIRED']}")
    print(f"LICENSE_NOT_DETECTED  : {summary['LICENSE_NOT_DETECTED']}")
    print(f"INVALID_LICENSE_DATA  : {summary['INVALID_LICENSE_DATA']}")
    print("==============================================")
    print("")
    
    # Print review candidates
    print("Review candidates:")
    print("----------------------------------------------")

    review_count = 0

    for result in results:
        if result["status"] in {
            "REVIEW_REQUIRED",
            "LICENSE_NOT_DETECTED",
            "INVALID_LICENSE_DATA",
        }:
            print(
                f"{result['package']} "
                f"{result['version']} "
                f"-> {result['license']} "
                f"[{result['status']}]"
            )

            review_count += 1

            if review_count >= 50:
                print("... showing first 50 candidates")
                break

    print("")

    # Do not fail the pipeline yet.
    # We want to review the results first.
    sys.exit(0)


if __name__ == "__main__":
    main()
