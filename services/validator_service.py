from typing import Dict, Tuple, List


def validate_bilingual_document(doc_data: dict, extracted_fields: dict) -> Tuple[bool, List[str]]:
    """
    Validates generated bilingual documents before PDF generation.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    en = doc_data.get('english_application', {})
    regional = doc_data.get('regional_language', {})
    lang = doc_data.get('language_primary', 'hi')
    en_body = en.get('body', '')
    reg_body = regional.get('body', '')

    # Rule 1: English must have NO Devanagari characters (U+0900–U+097F)
    dev_in_en = [c for c in en_body if 0x0900 <= ord(c) <= 0x097F]
    if dev_in_en:
        errors.append(f'English document contains {len(dev_in_en)} Devanagari character(s). Translation is incomplete.')

    # Rule 2: English must have NO Bengali characters (U+0980–U+09FF)
    ben_in_en = [c for c in en_body if 0x0980 <= ord(c) <= 0x09FF]
    if ben_in_en:
        errors.append(f'English document contains {len(ben_in_en)} Bengali character(s). Translation is incomplete.')

    # Rule 3: Regional doc must use its own script substantially
    if lang in ('hi', 'mr'):
        dev_count = sum(1 for c in reg_body if 0x0900 <= ord(c) <= 0x097F)
        total_alpha = sum(1 for c in reg_body if c.isalpha())
        if total_alpha > 50 and dev_count < total_alpha * 0.25:
            errors.append(f'Selected language ({lang}) document has insufficient Devanagari script.')
    elif lang == 'bn':
        ben_count = sum(1 for c in reg_body if 0x0980 <= ord(c) <= 0x09FF)
        total_alpha = sum(1 for c in reg_body if c.isalpha())
        if total_alpha > 50 and ben_count < total_alpha * 0.25:
            errors.append('Bengali document has insufficient Bengali script.')

    # Rule 4: Key facts must appear in English doc
    district = extracted_fields.get('district', '')
    state = extracted_fields.get('state', '')
    if district and len(district) > 2 and district.lower() not in en_body.lower():
        errors.append(f'District "{district}" not found in English document.')
    if state and len(state) > 2 and state.lower() not in en_body.lower():
        errors.append(f'State "{state}" not found in English document.')

    # Rule 5: English must be substantive
    if len(en_body.strip()) < 80:
        errors.append('English document is too short. Generation may have failed.')

    # Rule 6: No forbidden phrases
    for phrase in ['Government Approved', 'Legally Verified', 'Government Certified']:
        if phrase in en_body:
            errors.append(f'Forbidden phrase "{phrase}" found in English document.')

    return len(errors) == 0, errors
