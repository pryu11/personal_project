"""Manual employer name overrides.

etl.clean.standardize_employer_name() handles generic cleanup (case,
legal-entity suffixes like "Inc."/"LLC"). This dict fixes the cases that
generic cleanup can't -- stylized brand casing (e.g. "PayPal", "eBay",
"TikTok") that no rule can guess. Keyed by the generically-cleaned name,
built by reviewing the top ~150 employers by row count in the FY2025
CA tech-role dataset -- not exhaustive, and unmapped names simply pass
through unchanged rather than being dropped.
"""

EMPLOYER_NAME_OVERRIDES = {
    "Ibm": "IBM",
    "Nvidia": "NVIDIA",
    "Paypal": "PayPal",
    "Bytedance": "ByteDance",
    "Tiktok": "TikTok",
    "Tiktok U.S. Data Security": "TikTok U.S. Data Security",
    "Linkedin": "LinkedIn",
    "Servicenow": "ServiceNow",
    "Doordash": "DoorDash",
    "Ebay": "eBay",
    "Docusign": "DocuSign",
    "Vmware": "VMware",
    "Mongodb": "MongoDB",
    "Hcl America": "HCL America",
    "Ust Global": "UST Global",
    "Sap Labs": "SAP Labs",
    "Openai Opco": "OpenAI Opco",
    "Kla": "KLA",
    "Emc": "EMC",
    "Zs Associates": "ZS Associates",
    "Ltimindtree": "LTIMindtree",
    "Pricewaterhousecoopers Advisory Services": "PricewaterhouseCoopers Advisory Services",
    "Amazon.Com Services": "Amazon.com Services",
}
