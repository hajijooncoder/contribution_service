from typing import Tuple
from urllib.parse import urlparse

# Whitelist of strictly official Iranian legal & judicial authorities
OFFICIAL_LEGAL_DOMAINS = {
    # 1. Official Gazette of the Islamic Republic of Iran (Highest Authority)
    "rooznamehrasmi.ir": "روزنامه رسمی جمهوری اسلامی ایران",
    "www.rooznamehrasmi.ir": "روزنامه رسمی جمهوری اسلامی ایران",
    
    # 2. Islamic Parliament Research Center
    "rc.majlis.ir": "مرکز پژوهش‌های مجلس شورای اسلامی",
    "www.rc.majlis.ir": "مرکز پژوهش‌های مجلس شورای اسلامی",
    "majlis.ir": "مجلس شورای اسلامی",
    "www.majlis.ir": "مجلس شورای اسلامی",

    # 3. National Laws and Regulations System
    "qavanin.ir": "سامانه ملی قوانین و مقررات جمهوری اسلامی ایران",
    "www.qavanin.ir": "سامانه ملی قوانین و مقررات جمهوری اسلامی ایران",

    # 4. Presidency Laws & Regulations Portal (DOTIC)
    "dotic.ir": "معاونت تدوین، تنقیح و انتشار قوانین و مقررات ریاست جمهوری",
    "www.dotic.ir": "معاونت تدوین، تنقیح و انتشار قوانین و مقررات ریاست جمهوری",

    # 5. Judicial Research Institute & National Case Law Portal
    "ara.jri.ac.ir": "سامانه ملی آرای قضایی (پژوهشگاه قوه قضاییه)",
    "jri.ac.ir": "پژوهشگاه قوه قضاییه",
    "www.jri.ac.ir": "پژوهشگاه قوه قضاییه",

    # 6. Official Judiciary Portals & Administrative Court
    "adliran.ir": "درگاه خدمات الکترونیک قضایی",
    "www.adliran.ir": "درگاه خدمات الکترونیک قضایی",
    "divan-edalat.ir": "دیوان عدالت اداری",
    "www.divan-edalat.ir": "دیوان عدالت اداری",
    "eadl.ir": "درگاه یکپارچه قوه قضاییه",
    "www.eadl.ir": "درگاه یکپارچه قوه قضاییه",
    "judiciary.ir": "قوه قضاییه جمهوری اسلامی ایران",
    "www.judiciary.ir": "قوه قضاییه جمهوری اسلامی ایران",
}

def validate_official_legal_source_url(url: str) -> Tuple[bool, str, str]:
    """
    Validates whether the provided source URL originates from an authorized official
    governmental, parliamentary, or judicial authority portal.
    
    Returns:
        (is_valid, authority_name, error_reason)
    """
    if not url or not isinstance(url, str):
        return False, "", "آدرس اینترنتی مرجع الزامی است."

    clean_url = url.strip()
    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url

    try:
        parsed = urlparse(clean_url)
        hostname = (parsed.hostname or "").lower()
    except Exception:
        return False, "", "فرمت آدرس اینترنتی نامعتبر است."

    if not hostname:
        return False, "", "دامنه آدرس اینترنتی نامعتبر است."

    # Direct match or subdomain match
    matched_authority = OFFICIAL_LEGAL_DOMAINS.get(hostname)
    if not matched_authority:
        # Check parent domain match (e.g. sub.dotic.ir)
        for domain, auth_title in OFFICIAL_LEGAL_DOMAINS.items():
            if hostname.endswith("." + domain):
                matched_authority = auth_title
                break

    if not matched_authority:
        allowed_list_str = "روزنامه رسمی (rooznamehrasmi.ir)، مرکز پژوهش‌ها (rc.majlis.ir)، قوانین (qavanin.ir)، داتیک (dotic.ir) یا سامانه آرای قضایی (ara.jri.ac.ir)"
        return False, "", f"مرجع نامعتبر است. تنها مراجع رسمی و حاکمیتی کشور مجاز هستند: {allowed_list_str}"

    return True, matched_authority, ""
