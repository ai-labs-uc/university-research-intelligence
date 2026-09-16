-- =====================================
-- SEED: OPPORTUNITY SOURCES
-- =====================================

INSERT INTO opportunity_sources
(
    code,
    name,
    base_url,
    source_type,
    trust_level,
    enabled,
    created_at
)
VALUES

(
    'DOST-PCIEERD',
    'DOST Philippine Council for Industry, Energy and Emerging Technology Research and Development',
    'https://pcieerd.dost.gov.ph/',
    'HTML',
    'OFFICIAL_AGENCY',
    1,
    NOW()
),

(
    'DOST-PCHRD',
    'DOST Philippine Council for Health Research and Development',
    'https://pchrd.dost.gov.ph/',
    'HTML',
    'OFFICIAL_AGENCY',
    1,
    NOW()
),

(
    'DOST-PCAARRD',
    'DOST Philippine Council for Agriculture, Aquatic and Natural Resources Research and Development',
    'https://pcaarrd.dost.gov.ph/',
    'HTML',
    'OFFICIAL_AGENCY',
    1,
    NOW()
),

(
    'CHED',
    'Commission on Higher Education Research Programs',
    'https://ched.gov.ph/',
    'HTML',
    'OFFICIAL_AGENCY',
    1,
    NOW()
),

(
    'NRCP',
    'National Research Council of the Philippines',
    'https://nrcp.dost.gov.ph/',
    'HTML',
    'OFFICIAL_AGENCY',
    1,
    NOW()
),

(
    'SEI',
    'DOST Science Education Institute',
    'https://sei.dost.gov.ph/',
    'HTML',
    'OFFICIAL_AGENCY',
    1,
    NOW()
),

(
    'ACM',
    'Association for Computing Machinery',
    'https://www.acm.org/',
    'HTML',
    'OFFICIAL_PUBLISHER',
    1,
    NOW()
),

(
    'WIKICFP',
    'WikiCFP Research Calls',
    'http://www.wikicfp.com/',
    'HTML',
    'AGGREGATOR',
    1,
    NOW()
);



-- =====================================
-- SEED: SAMPLE RESEARCH OPPORTUNITIES
-- =====================================

INSERT INTO research_opportunities
(
    source_id,
    opportunity_type,
    title,
    organization,
    summary,
    eligibility,
    topics,
    country,
    currency,
    source_url,
    canonical_url,
    status,
    verification_status,
    discovered_at,
    updated_at
)
VALUES


(
    1,
    'GRANT',
    'Research Grants for Emerging Technology Projects',
    'DOST-PCIEERD',
    'Funding opportunity for research projects involving industry, energy, and emerging technologies.',
    'Researchers from recognized academic institutions and research organizations.',
    '["Artificial Intelligence","Technology","Innovation"]',
    'Philippines',
    'PHP',
    'https://pcieerd.dost.gov.ph/',
    'https://pcieerd.dost.gov.ph/',
    'OPEN',
    'VERIFIED',
    NOW(),
    NOW()
),


(
    2,
    'GRANT',
    'Health Research Innovation Grant Program',
    'DOST-PCHRD',
    'Research funding support for health-related innovation and development.',
    'Academic researchers and health research institutions.',
    '["Health","Medicine","Biomedical Research"]',
    'Philippines',
    'PHP',
    'https://pchrd.dost.gov.ph/',
    'https://pchrd.dost.gov.ph/',
    'OPEN',
    'VERIFIED',
    NOW(),
    NOW()
),


(
    3,
    'GRANT',
    'Agriculture and Natural Resources Research Funding',
    'DOST-PCAARRD',
    'Supports research and development projects in agriculture, aquatic resources, and natural resources.',
    'Researchers affiliated with recognized institutions.',
    '["Agriculture","Environment","Food Security"]',
    'Philippines',
    'PHP',
    'https://pcaarrd.dost.gov.ph/',
    'https://pcaarrd.dost.gov.ph/',
    'OPEN',
    'VERIFIED',
    NOW(),
    NOW()
),


(
    4,
    'GRANT',
    'CHED Research Development Program',
    'Commission on Higher Education',
    'Research support program for higher education institutions.',
    'Faculty researchers from eligible universities.',
    '["Education","Social Science","Innovation"]',
    'Philippines',
    'PHP',
    'https://ched.gov.ph/',
    'https://ched.gov.ph/',
    'OPEN',
    'VERIFIED',
    NOW(),
    NOW()
),


(
    7,
    'CALL_FOR_PAPER',
    'International Computing Research Conference Call',
    'Association for Computing Machinery',
    'International opportunity for researchers to submit scholarly papers.',
    'Researchers and academics in computing-related disciplines.',
    '["Computer Science","AI","Software Engineering"]',
    'International',
    NULL,
    'https://www.acm.org/',
    'https://www.acm.org/',
    'OPEN',
    'VERIFIED',
    NOW(),
    NOW()
);



-- =====================================
-- VERIFY DATA
-- =====================================

SELECT COUNT(*) AS source_count
FROM opportunity_sources;


SELECT COUNT(*) AS opportunity_count
FROM research_opportunities;