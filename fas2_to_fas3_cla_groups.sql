-- Insert a new license agreement we will port the old one to

INSERT INTO license_agreement (
    "name", status, content, comment, enabled_at_signup,
    creation_timestamp, update_timestamp)
VALUES (
    'cla_fpca',
    1,
    'License agreement text to update later',
    'Fedora Project Contributor agreement',
    TRUE,
    NOW(),
    NOW()
);

-- Insert everyone who signed the cla_fpca from FAS2 as signing the new LA in FAS3

INSERT INTO signed_license_agreement (
    license_id, person_id)
SELECT license_agreement.id, people.id
FROM license_agreement, people,  group_membership, groups
WHERE groups.name = 'cla_fpca'
AND groups.id = group_membership.group_id
AND people.id = group_membership.person_id
AND license_agreement.name = 'cla_fpca';


--
-- Here below are a set of queries that can be used to debug things
--


-- -- For the record, find all the *CLA* groups

-- SELECT * FROM groups WHERE "name" LIKE '%cla%' OR "name" = 'fpca';

-- -- Get all the people who that are in the group 'cla_fpca'

-- SELECT people.* FROM people, group_membership, groups
-- WHERE groups.name = 'cla_fpca'
-- AND groups.id = group_membership.group_id
-- AND people.id = group_membership.person_id;



-- -- Check which groups 'pingou' is a member of
-- SELECT groups.* FROM people, group_membership, groups
-- WHERE groups.id = group_membership.group_id
-- AND people.id = group_membership.person_id
-- AND people.username = 'pingou';

-- -- Check which CLA pingou has signed
-- SELECT groups.* FROM people, group_membership, groups
-- WHERE groups.id = group_membership.group_id
-- AND people.id = group_membership.person_id
-- AND groups.name LIKE '%cla%'
-- AND people.username = 'pingou';

-- -- Check which LA 'pingou' has signed

-- SELECT license_agreement.*
-- FROM people, license_agreement, signed_license_agreement
-- WHERE license_agreement.id = signed_license_agreement.license_id
-- AND people.id = signed_license_agreement.person_id
-- AND people.username = 'pingou';
