from authority_lookup import (
    PMC_URL, PCMC_URL, STATE_GRIEVANCE_URL,
    PMC_ROAD_MITRA_URL, PCMC_POTHOLE_APP_URL,
    suggest_authority, contractor_status, alternate_channels,
)


def test_pune_keyword_is_cautious_and_has_official_reporting_channel():
    result = suggest_authority("Kothrud, Pune, Maharashtra")
    assert "PMC may be relevant" in result["authority"]
    assert result["url"] == PMC_URL
    assert result["reporting_url"] == PMC_ROAD_MITRA_URL
    assert "not a jurisdiction" in result["note"]
    assert "not a complaint form" in result["note"]


def test_pcmc_keyword_uses_pcmc_channel():
    result = suggest_authority("Wakad, Pimpri-Chinchwad, Maharashtra")
    assert "PCMC may be relevant" in result["authority"]
    assert result["url"] == PCMC_URL
    assert result["reporting_url"] == PCMC_POTHOLE_APP_URL


def test_unknown_area_does_not_default_to_pmc():
    result = suggest_authority("Somewhere in Maharashtra")
    assert result["url"] == STATE_GRIEVANCE_URL
    assert result["reporting_url"] is None
    assert "confirm the exact road owner" in result["note"].casefold()


def test_no_contractor_is_invented():
    result = contractor_status("Paud Road, Pune")
    assert "No verified" in result["status"]
    assert result["url"] == "https://mahatenders.gov.in/"


def test_alternate_channels_exclude_primary():
    assert all(url != PMC_URL for _, url in alternate_channels(PMC_URL))
