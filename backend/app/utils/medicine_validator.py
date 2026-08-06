import re
import urllib.request
import urllib.parse
import json

# Curated set of common medicines, generic names, brand names, and dosage forms
KNOWN_MEDICINES = {
    "paracetamol", "acetaminophen", "ibuprofen", "aspirin", "amoxicillin", "lipitor", "metformin",
    "atorvastatin", "omeprazole", "cetirizine", "loratadine", "azithromycin", "doxycycline",
    "ciprofloxacin", "levothyroxine", "albuterol", "salbutamol", "inhaler", "hydrochlorothiazide",
    "gabapentin", "losartan", "sertraline", "furosemide", "prednisone", "pantoprazole",
    "montelukast", "escitalopram", "rosuvastatin", "clopidogrel", "tramadol", "morphine",
    "codeine", "penicillin", "augmentin", "tylenol", "advil", "motrin", "aleve", "xanax",
    "valium", "ativan", "klonopin", "prozac", "zoloft", "lexapro", "celexa", "effexor",
    "cymbalta", "wellbutrin", "seroquel", "abilify", "risperdal", "zyprexa", "lamictal",
    "depakote", "topamax", "keppra", "neurontin", "lyrica", "zofran", "phenergan", "imodium",
    "miralax", "colace", "nexium", "prevacid", "prilosec", "protonix", "pepcid", "tums",
    "multivitamin", "vitamin c", "vitamin d", "vitamin b12", "iron", "calcium", "zinc",
    "insulin", "eye drops", "ear drops", "cough syrup", "nasal spray", "antacid",
    "benadryl", "allegra", "zyrtec", "claritin", "flonase", "sudafed", "mucinex", "vicks",
    "dextromethorphan", "guaifenesin", "pseudoephedrine", "diphenhydramine", "chlorpheniramine",
    "famotidine", "ranitidine", "simethicone", "loperamide", "bismuth", "aspirin 81mg"
}

def validate_medicine_name(name: str) -> tuple[bool, str]:
    """
    Validates entered medicine name.
    Returns (is_valid, error_message).
    If medicine is not recognized as legitimate, returns False and friendly validation message.
    """
    if not name or not name.strip():
        return False, "Medicine name is required."

    cleaned_name = name.strip().lower()

    # Reject obvious invalid patterns: single char, pure numbers, or keyboard mashes
    if len(cleaned_name) < 2:
        return False, "The entered medicine could not be verified. Please check the spelling or enter a valid medicine."

    if cleaned_name.isdigit():
        return False, "The entered medicine could not be verified. Please check the spelling or enter a valid medicine."

    # Check for repetitive gibberish patterns like "asdfghjkl", "qwerty", "aaaaa"
    gibberish_patterns = [r"^[a-z]{1,2}$", r"(.)\1{3,}", r"^asdf", r"^qwerty", r"^zxcv"]
    for pattern in gibberish_patterns:
        if re.search(pattern, cleaned_name):
            return False, "The entered medicine could not be verified. Please check the spelling or enter a valid medicine."

    # Check local curated set first (fast path)
    base_words = re.findall(r'[a-zA-Z]+', cleaned_name)
    if any(word in KNOWN_MEDICINES for word in base_words) or cleaned_name in KNOWN_MEDICINES:
        return True, ""

    # Query NIH RxNorm API for real-world verification
    try:
        encoded_term = urllib.parse.quote(cleaned_name)
        # 1. Try RxNorm exact match
        url_exact = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={encoded_term}"
        req = urllib.request.Request(url_exact, headers={"User-Agent": "PillsyncValidator/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get("idGroup", {}).get("rxnormId"):
                return True, ""

        # 2. Try RxNorm approximate term search
        url_approx = f"https://rxnav.nlm.nih.gov/REST/approximateTerm.json?term={encoded_term}&maxEntries=5"
        req_approx = urllib.request.Request(url_approx, headers={"User-Agent": "PillsyncValidator/1.0"})
        with urllib.request.urlopen(req_approx, timeout=3) as resp:
            data_approx = json.loads(resp.read().decode('utf-8'))
            candidates = data_approx.get("approximateGroup", {}).get("candidate", [])
            if candidates and len(candidates) > 0:
                # Found candidate match in medical database
                return True, ""
    except Exception as e:
        print(f"⚠️ [RxNorm API Warning] Query failed/timed out: {e}. Falling back to strict structural validation.")

    # Fallback heuristic: If name contains at least 3 alphabetic chars and doesn't match obvious junk,
    # but RxNorm returned nothing and local dictionary didn't match, verify word structure.
    # Common medicine suffixes / roots
    med_suffixes = (
        "cillin", "mycin", "cycline", "statin", "prazole", "tidine", "fenac", "profine", "profen",
        "olol", "alol", "pril", "sartan", "dipine", "zosin", "xaban", "parin", "grel", "plase",
        "mab", "nib", "gib", "cept", "tide", "gliptin", "glutide", "gliflozin", "glitazone",
        "azine", "pramine", "triptyline", "triptan", "dronate", "lukast", "tropium", "oterol",
        "sonide", "solone", "onide", "nida", "zole", "bendazole", "vir", "vudine", "navir",
        "caine", "terol", "pressin", "relin", "stat", "stene", "gest", "estrel", "diol",
        "phine", "codone", "morphone", "pam", "lam", "barb", "cain", "drine", "phedrine",
        "amine", "tine", "zine", "sone", "trol", "pium", "ine", "ol", "ate", "ide"
    )
    
    if len(base_words) > 0 and any(w.endswith(med_suffixes) for w in base_words):
        return True, ""

    # If it reached here without matching any medical DB or pattern, return validation failure
    return False, "The entered medicine could not be verified. Please check the spelling or enter a valid medicine."
