from app.auth.ids import email_domain, hash_email


def test_hash_email_is_deterministic():
    assert hash_email("alice@gju.edu.jo", "p1") == hash_email("alice@gju.edu.jo", "p1")
    assert hash_email("alice@gju.edu.jo", "p1") != hash_email("alice@gju.edu.jo", "p2")


def test_email_domain_lowercased():
    assert email_domain("Bob@GJU.edu.JO") == "gju.edu.jo"
