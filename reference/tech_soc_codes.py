"""Curated SOC (Standard Occupational Classification) codes for tech/data roles.

Job titles in LCA data are employer-chosen and inconsistent, so we filter by
SOC code instead. Codes follow the 2018 SOC taxonomy, which is what recent
(FY2021+) LCA disclosure data uses.
"""

TECH_SOC_CODES = {
    "15-1211": "Computer Systems Analysts",
    "15-1212": "Information Security Analysts",
    "15-1221": "Computer and Information Research Scientists",
    "15-1231": "Computer Network Support Specialists",
    "15-1232": "Computer User Support Specialists",
    "15-1241": "Computer Network Architects",
    "15-1244": "Network and Computer Systems Administrators",
    "15-1251": "Computer Programmers",
    "15-1252": "Software Developers",
    "15-1253": "Software Quality Assurance Analysts and Testers",
    "15-1254": "Web Developers",
    "15-1255": "Web and Digital Interface Designers",
    "15-1299": "Computer Occupations, All Other",
    "15-2011": "Actuaries",
    "15-2031": "Operations Research Analysts",
    "15-2041": "Statisticians",
    "15-2051": "Data Scientists",
}
