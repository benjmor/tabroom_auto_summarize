# This is based off of Palmer's https://github.com/speechanddebate/tabroom/blob/master/web/funclib/short_name.mas
import re


def remove_suffix(input_string, suffix_to_remove):
    # Check if the string ends with the specified suffix
    if re.search(suffix_to_remove + "$", input_string):
        # Remove the suffix from the string
        result_string = input_string[: -len(suffix_to_remove)].strip()
        return result_string
    else:
        return input_string


def remove_prefix(input_string, prefix_to_remove):
    # Check if the string ends with the specified prefix
    if re.search("^" + prefix_to_remove, input_string):
        # Remove the suffix from the string
        result_string = input_string[len(prefix_to_remove) :].strip()
        return result_string
    else:
        return input_string


def resolve_longname_to_shortname(long_name: str):
    """
    This function takes a long name and returns a short name.
    """
    # These are special cases that don't play nice with the logic
    special_case_dict = {
        "thomas jefferson high school of science and technology": "Thomas Jefferson",
        "thomas jefferson high school of science & technology": "Thomas Jefferson",
        "the bronx high school of science": "Bronx Science",
        "whitney m. young magnet high school": "Whitney Young",
        "lane tech college prep h.s.": "Lane Tech",
        "new school": "New School",
        "the new school": "New School",
        "bc academy": "BC Academy",
        "new york university": "NYU",
        "boston college": "Boston College",
        "boston university": "Boston University",
        "air academy high school": "Air Academy",
        "air academy hs": "Air Academy",
        "college prep school": "College Prep",
        "college prep hs": "College Prep",
        "st. paul academy and summit school": "St. Paul Academy and Summit",
        "university high school, irvine": "University HS, Irvine",
        "alannah debates": "Alannah",
        "bellarmine college preparatory": "Bellarmine College Prep",
        "basis independent fremont(hs)": "Basis Independent Fremont",
        "brooks debate institute": "Brooks Debate",
        "the delores taylor arthur school for young men": "Delores Taylor Arthur School for Young Men",
        "dhs independent": "DHS",
        "damien high school and st lucy's priory": "Damien HS and St. Lucy's Priory",
        "davidson academy online": "Davidson Academy",
        "st. ignatius college prep": "St Ignatius College Prep",
        "vegas debates": "Vegas Debates",
        "young genius, bay area speech and debate": "Young Genius",
    }
    if long_name.lower() in special_case_dict:
        return special_case_dict[long_name.lower()]

    # Disambiguate between similarly-named schools
    milton_high_list = [
        "Milton High School",
        "MiltonHigh",
        "Milton HS",
        "Milton Hi",
    ]
    milton_acad_list = ["Milton Academy", "MiltonAcademy", "Milton AC"]
    cary_high_list = ["Cary High School", "Cary HS", "Cary Hi"]
    cary_acad_list = ["Cary Academy", "Cary AC"]
    if long_name in milton_high_list:
        return "Milton High"
    if long_name in milton_acad_list:
        return "Milton Acad"
    if long_name in cary_high_list:
        return "Cary High"
    if long_name in cary_acad_list:
        return "Cary Acad"

    # ALWAYS REMOVE
    always_remove = ["Junior-Senior", "Charter Public", "Public Charter"]
    for remove_phrase in always_remove:
        long_name = long_name.replace(remove_phrase, "")

    # Replace "High School Independent" with "Independent"
    long_name = long_name.replace("High School Independent", "Independent")

    # ELIMINATE THESE PHRASES ENTIRELY IF THEY APPEAR AT THE END
    bad_endings = [
        "Mock Trial",
        "Debate Association",
        "Debate Academy",
        "Debate Panel",
        "Debate Society",
        "Debating Society",
        "Forensics/Debate",
        "of Math and Science",
        "Academy",
        "Early College High School",
        "Regional High School",
        "Middle School",
        "Junior High School",
        "Upper School",
        "Sr High School",
        "University High School",
        "High School",
        "College Prepatory",
        "College Prep",
        "Colleges",
        "School",
        "school",
        "Schools",
        "schools",
        " High",
        "H.S",
        "HS",
        "M.S",
        "MS",
        "(MS)",
        "JH",
        "Jr",
        "JR",
        " Middle",
        "(Middle)",
        "Elementary",
        "(Elementary)",
        "Intermediate",
        "Community",
        "(Intermediate)",
        "Junior",
        "(Middle)",
        "Regional",
        "Academy",
        "School for Young Men",
        "School",
        "school",
        "Schools",
        "schools",
        "Sr",
        "Sr High School",
        "sr",
        "Club",
        "Team",
        "Society",
        "Speech and Debate",
        "Forensics",
        "Forensic",
        "Speech",
        "Debate",
        "Parliamentary",
        "University",
        "CP",
        "College",
        "CC",
    ]
    for bad_ending in bad_endings:
        if re.search(rf"{bad_ending}$", long_name, re.IGNORECASE):
            long_name = long_name.replace(bad_ending, "")
            break

    shortening_dict = {
        "Middle School of the Arts": "Arts",
        "School of the Arts": "Arts",
        "Preparatory": "Prep",
        "Technological": "Tech",
        "Technology": "Tech",
        "California State University": "CSU",
        "California State University,": "CSU",
        "Community College": "Community",
        "State University": "State",
        "State University,": "State",
        "Saint": "St",
        "St.": "St",
    }
    for long_version in shortening_dict:
        if re.search(long_version, long_name, re.IGNORECASE):
            long_name = long_name.replace(long_version, shortening_dict[long_version])
            break

    bad_beginnings = [
        "The",
        "The University of",
        "The University Of",
        "University of",
        "University Of",
        "The College of",
        "The College Of",
        "College of",
        "College Of,",
    ]
    for bad_beginning in bad_beginnings:
        if re.search(bad_beginning, long_name, re.IGNORECASE):
            long_name = long_name.replace(bad_beginning, "")
            break

    return long_name.strip()
