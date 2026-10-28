"""Conservative Pune-region authority and complaint-channel guidance.

Address keyword matching is only a hint, never proof of road ownership.
"""

PMC_URL = "https://www.pmc.gov.in/"
PCMC_URL = "https://www.pcmcindia.gov.in/"
PWD_TENDERS_URL = "https://mahatenders.gov.in/"
STATE_GRIEVANCE_URL = "https://grievances.maharashtra.gov.in/"

# Official app listings are useful starting points, but do not submit complaints themselves.
PMC_ROAD_MITRA_URL = "https://play.google.com/store/apps/details?id=com.nyatitechnologies.pmcroadmitra"
PCMC_POTHOLE_APP_URL = "https://play.google.com/store/apps/details?id=io.framework7.pcmcpotholemanagement"


def suggest_authority(address: str | None, latitude=None, longitude=None):
    """Return cautious authority guidance plus an official reporting-channel starting point."""
    text = (address or "").casefold()
    pcmc_terms = ("pimpri", "chinchwad", "nigdi", "akurdi", "bhosari", "moshi", "wakad", "ravet", "thergaon")
    pune_terms = ("pune", "shivajinagar", "kothrud", "hadapsar", "kondhwa", "baner", "aundh", "warje", "katraj", "swargate")
    if any(term in text for term in pcmc_terms):
        return {
            "authority": "PCMC may be relevant (verify road ownership)",
            "url": PCMC_URL,
            "reporting_url": PCMC_POTHOLE_APP_URL,
            "reporting_label": "PCMC Pothole Management app (Google Play)",
            "note": "Address keywords suggest the Pimpri-Chinchwad area. This is not a jurisdiction determination; check the road owner before filing. The app link opens its official app listing, not a complaint form.",
        }
    if any(term in text for term in pune_terms):
        return {
            "authority": "PMC may be relevant (verify road ownership)",
            "url": PMC_URL,
            "reporting_url": PMC_ROAD_MITRA_URL,
            "reporting_label": "PMC Road Mitra app (Google Play)",
            "note": "Address keywords suggest Pune city, but this is not a jurisdiction determination. State highways, PWD roads, cantonment roads, and private roads may have different owners. The app link opens its official app listing, not a complaint form.",
        }
    return {
        "authority": "Not determined — confirm the road owner",
        "url": STATE_GRIEVANCE_URL,
        "reporting_url": None,
        "reporting_label": None,
        "note": "No reliable municipal jurisdiction match was found. Confirm the exact road owner before filing. The Maharashtra grievance portal is a general starting point, not a pothole-specific form or a claim of responsibility.",
    }


def contractor_status(address: str | None):
    """No verified road-specific tender data ships with this prototype."""
    return {
        "status": "No verified road-specific contractor record included",
        "note": "Contractor details are intentionally not guessed. Check the official Maharashtra e-Tenders portal and match the exact road/work package before attributing responsibility.",
        "url": PWD_TENDERS_URL,
    }


def alternate_channels(primary_url: str):
    """Official authority homepages, excluding the primary URL."""
    channels = [
        ("Pune Municipal Corporation", PMC_URL),
        ("Pimpri-Chinchwad Municipal Corporation", PCMC_URL),
        ("Maharashtra State Grievance Portal", STATE_GRIEVANCE_URL),
    ]
    return [(name, url) for name, url in channels if url != primary_url]


def ownership_is_uncertain(authority_text: str) -> bool:
    """Keyword matching never proves ownership, so this is True for every current outcome."""
    return True
