from fas.model import *

def people_query(constraints=None, columns=None):
    people_columns = [c.name for c in PeopleTable.columns]

    column_map = {
        'id': PeopleTable.c.id,
        'username': PeopleTable.c.username,
        'human_name': PeopleTable.c.human_name,
        'gpg_keyid': PeopleTable.c.gpg_keyid,
        'ssh_key': PeopleTable.c.ssh_key,
        'email': PeopleTable.c.email,
        'country_code': PeopleTable.c.country_code,
        'creation': PeopleTable.c.creation,
        'ircnick': PeopleTable.c.ircnick,
        'status': PeopleTable.c.status,
        'locale': PeopleTable.c.locale,
        'timezone': PeopleTable.c.timezone,
        'latitude': PeopleTable.c.latitude,
        'longitude': PeopleTable.c.longitude,
        'group': GroupsTable.c.name,
        'group_type': GroupsTable.c.group_type,
        'role_status': PersonRolesTable.c.role_status,
        'role_type': PersonRolesTable.c.role_type,
    }

    if constraints is None:
        constraints = {}

    # By default, return all of the people columns in column_map.
    if columns is None:
        columns = [c for c in people_columns if c in column_map]

    groupjoin = []
    if 'group' in constraints \
        or 'group_type' in constraints \
        or 'role_status' in constraints \
        or 'role_type' in constraints:
        groupjoin = [PeopleTable.join(PersonRolesTable,
            PersonRolesTable.c.person_id == PeopleTable.c.id).join(GroupsTable,
            GroupsTable.c.id == PersonRolesTable.c.group_id)]

    try:
        query = select([column_map[c] for c in columns], from_obj=groupjoin)
    except KeyError:
        raise ValueError # Invalid column requested!

    for k, v in constraints.iteritems():
        if k not in column_map:
            raise ValueError # Invalid query!
        query = query.where(column_map[k].like(v))

    results = query.execute().fetchall()
    return [dict(zip(columns, r)) for r in results]
