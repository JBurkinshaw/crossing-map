"""crossing.photo_assets: credits as plain text, the episode a photo's words are safe from, and the WebP files."""

import io

from PIL import Image

from crossing import photo_assets
from crossing.photo_assets import clean_date, licence_url, plain, safe_from, slug, to_webp


def test_plain_drops_hidden_text_and_tags():
    artist = ('<div class="fn value"> Unknown author<span style="display: none;">Unknown author</span>'
              ' or not provided</div>')
    assert plain(artist) == "Unknown author or not provided"
    flickr = '<a class="external text" href="https://flickr.com/x">Patrick Alexander</a> from Las Cruces, NM'
    assert plain(flickr) == "Patrick Alexander from Las Cruces, NM"
    assert plain('The original uploader was <a href="#">Willjay</a> at <a href="#">English Wikipedia</a>.') == (
        "The original uploader was Willjay at English Wikipedia.")


def test_clean_date_keeps_the_day_only():
    assert clean_date("2015-04-01 20:53") == "2015-04-01"
    assert clean_date("1 June 2010 (according to Exif data)") == "1 June 2010"
    assert clean_date("Taken on 6 February 2006, 22:27:15") == "6 February 2006"
    assert clean_date("1995 – 2013") == "1995 – 2013"
    assert clean_date("") is None


def test_licence_url_over_https_and_none_for_public_domain():
    assert licence_url("http://creativecommons.org/publicdomain/zero/1.0/deed.en") == (
        "https://creativecommons.org/publicdomain/zero/1.0/deed.en")
    assert licence_url("") is None


def test_safe_from_waits_for_the_latest_place_named():
    named = [("Animas Valley", "1-03"), ("Lordsburg", "2-05"), ("Bisbee", ""), ("Paquimé", "2-08")]
    assert safe_from("Northern Lordsburg Mesa - Flickr", named) == "2-05"
    assert safe_from("Paquimé (ruinas), near Lordsburg", named) == "2-08"
    # A name held in one met earlier counts as met: "Animas" in the Animas Valley.
    assert safe_from("Animas New Mexico", named + [("Animas", "4-01")]) == "1-03"
    # Context places show from the start, and a name inside another word is not a match.
    assert safe_from("Bisbee Arizona", named) == ""
    assert safe_from("Lordsburgers", named) == ""


def test_to_webp_shrinks_to_the_long_side_and_drops_metadata():
    exif = Image.Exif()
    exif[0x010F] = "A camera"  # Make
    exif[0x0112] = 6  # Orientation: rotate 90 degrees, so the file is turned upright first
    src = io.BytesIO()
    Image.new("RGB", (1200, 800), "white").save(src, "JPEG", exif=exif.tobytes())
    data, w, h = to_webp(src.getvalue())
    assert (w, h) == (427, photo_assets.LONG_SIDE)
    with Image.open(io.BytesIO(data)) as im:
        assert im.format == "WEBP" and im.size == (w, h)
        assert not im.info.get("exif") and not im.info.get("icc_profile") and not im.info.get("xmp")


def test_file_names_are_readable_and_stable():
    row = {"file_title": "Vista de Temósachic, Chihuahua",
           "commons_url": "https://commons.wikimedia.org/wiki/File:Vista_de_Tem%C3%B3sachic,_Chihuahua.jpg"}
    assert slug(row["file_title"]) == "vista-de-temosachic-chihuahua"
    assert photo_assets.file_name(row) == photo_assets.file_name(dict(row))
    assert photo_assets.file_name(row).startswith("vista-de-temosachic-chihuahua-")
