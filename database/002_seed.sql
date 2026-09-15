
INSERT INTO opportunity_sources
(code, name, base_url, source_type, trust_level)
VALUES
('PCIEERD', 'DOST-PCIEERD', 'https://pcieerd.dost.gov.ph/', 'HTML', 'OFFICIAL_AGENCY'),
('PCHRD', 'DOST-PCHRD', 'https://www.pchrd.dost.gov.ph/', 'HTML', 'OFFICIAL_AGENCY'),
('PCAARRD', 'DOST-PCAARRD', 'https://pcaarrd.dost.gov.ph/', 'HTML', 'OFFICIAL_AGENCY'),
('NRCP', 'National Research Council of the Philippines', 'https://nrcp.dost.gov.ph/', 'HTML', 'OFFICIAL_AGENCY'),
('CHED', 'Commission on Higher Education', 'https://ched.gov.ph/', 'HTML', 'OFFICIAL_AGENCY'),
('SEI', 'DOST Science Education Institute', 'https://www.sei.dost.gov.ph/', 'HTML', 'OFFICIAL_AGENCY'),
('STARTUPGOVPH', 'Startup Innovations Portal', 'https://startup.gov.ph/', 'HTML', 'OFFICIAL_AGENCY'),
('TAPI', 'DOST-TAPI Technology Transfer', 'https://tapitechtransfer.dost.gov.ph/', 'HTML', 'OFFICIAL_AGENCY'),
('ACM', 'Association for Computing Machinery', 'https://www.acm.org/', 'HTML', 'OFFICIAL_PUBLISHER'),
('WIKICFP', 'WikiCFP', 'http://www.wikicfp.com/', 'HTML', 'AGGREGATOR')
ON DUPLICATE KEY UPDATE
name=VALUES(name);
