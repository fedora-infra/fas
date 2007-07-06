<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'"
    xmlns:mochi="MyUniqueMochiUri">

<head>
 <style type="text/css">
@import "/fas/static/css/fas.css";
@import '/fas/static/css/sortable_tables.css';
 </style>
</head>
<body>
<script src="/fas/static/javascript/sortable_tables.js" type="text/javascript"></script>
<h1>My Status: ${me.fedoraRoleStatus}</h1>
<form py:if="'Not a Member' in me.fedoraRoleStatus" action='applyForGroup'>
    <input type='hidden' name='groupName' value='${group.cn}'/>
    <input type='text' name='requestField' value='Please let me join..'/>
    <input type='submit' name='action' value='Join'/>
</form>
<a py:if="'Not a Member' not in me.fedoraRoleStatus" href="${tg.url('applyForGroup', groupName=group.cn, action='Remove')}">Remove me</a>
 

<h2>${group.cn}</h2>
<table>
<!--    <script language="JavaScript" type="text/JavaScript">
        AutoCompleteManager${field_id} = new AutoCompleteManager('${field_id}',
        '${text_field.field_id}', '${hidden_field.field_id}',
        '${search_controller}', '${search_param}', '${result_name}',${str(only_suggest).lower()},
        '${tg.url([tg.widgets, 'turbogears.widgets/spinner.gif'])}', ${complete_delay});
        addLoadEvent(AutoCompleteManager${field_id}.initialize);
    </script>
-->
    <tr><td>Name</td><td>${group.cn}</td></tr>
    <tr><td>Owner</td><td>${group.fedoraGroupOwner}</td></tr>
    <tr><td>Type</td><td>${group.fedoraGroupType}</td></tr>
    <tr><td>Needs Sponsor</td><td>${group.fedoraGroupNeedsSponsor}</td></tr>
    <tr><td>Self Removal</td><td>${group.fedoraGroupUserCanRemove}</td></tr>
    <tr><td>fedoraGroupJoinMsg</td><td>${group.fedoraGroupJoinMsg}</td></tr>
</table>

<h2 py:if='me.fedoraRoleStatus == "approved"'>Invite  <a href='' onClick="displayHelp('inviteToGroup'); return false;">(?)</a></h2>
<span py:if='me.fedoraRoleStatus == "approved"'>${searchUserForm(action='modifyGroup', value=value, method='get')}</span>


<h2>Members</h2>
<span>
<!--    <form action='modifyGroup'>
        <input type='hidden' name='groupName' value='${group.cn}'/>
        <input type='text' name='userName'/>
        <input type='submit' name='action' value='apply'/>
    </form>-->

</span>
<table id='sortable_table' class='datagrid'>
    <thead>
        <tr><th mochi:format="str">Username</th><th>Sponsor</th><th mochi:format="str">Date Added</th><th>Date Approved</th><th mochi:format="str">Approval</th><th>Role Type</th><th py:if='me.fedoraRoleType == "administrator" or me.fedoraRoleType == "sponsor"'>Action</th><th></th></tr>
    </thead>
    <tr py:for="user in groups">
        <td><a href='editAccount?userName=${user}'>${user}</a></td>
        <td py:if='not(groups[user].fedoraRoleSponsor ==  "None")'><a href='editAccount?userName=${groups[user].fedoraRoleSponsor}'>${groups[user].fedoraRoleSponsor}</a></td>
        <td py:if='groups[user].fedoraRoleSponsor == "None"'>${groups[user].fedoraRoleSponsor}</td>
        <td>${groups[user].fedoraRoleCreationDate}</td>
        <td>${groups[user].fedoraRoleApprovalDate}</td>
        <td>${groups[user].fedoraRoleStatus}</td>
        <td>${groups[user].fedoraRoleType}</td>
        <!--<td>${groups[user].fedoraRoleDomain}</td>-->

        <!-- This section includes all action items -->
        <td py:if='me.fedoraRoleType == "administrator"'>
            <a py:if="group.fedoraGroupNeedsSponsor.upper() == 'TRUE'" href="${tg.url('modifyGroup', groupName=groups[user].cn, userName=user, action='sponsor')}">Sponsor</a>
            <a py:if="not group.fedoraGroupNeedsSponsor.upper() == 'TRUE' and groups[user].fedoraRoleStatus.lower() != 'approved'" href="${tg.url('modifyGroup', groupName=groups[user].cn, userName=user, action='sponsor')}">Approve</a>
            <a href="${tg.url('modifyGroup', groupName=groups[user].cn, userName=user, action='remove')}">Delete</a>
            <a href="${tg.url('modifyGroup', groupName=groups[user].cn, userName=user, action='upgrade')}">Upgrade</a>
            <a href="${tg.url('modifyGroup', groupName=groups[user].cn, userName=user, action='downgrade')}">Downgrade</a> Suspend
        </td>
        <td py:if='me.fedoraRoleType == "sponsor" and not groups[user].fedoraRoleType == "administrator"'>
            <a href="${tg.url('modifyGroup', groupName=groups[user].cn, userName=user, action='sponsor')}" py:if="group.fedoraGroupNeedsSponsor.upper() == 'TRUE'">Sponsor</a>
            <a href="${tg.url('modifyGroup', groupName=groups[user].cn, userName=user, action='sponsor')}" py:if="not group.fedoraGroupNeedsSponsor.upper() == 'TRUE'">Approve</a>
            <a href="${tg.url('modifyGroup', groupName=groups[user].cn, userName=user, action='remove')}">Delete</a>
            <a py:if='groups[user].fedoraRoleType' href="${tg.url('modifyGroup', groupName=groups[user].cn, userName=user, action='upgrade')}">Upgrade</a>
            <a href="${tg.url('modifyGroup', groupName=groups[user].cn, userName=user, action='downgrade')}">Downgrade</a> Suspend
            <div py:if="'not' in '%s' % tg_flash and user in '%s' % tg_flash"> -- Error!</div>
        </td>
    </tr>
</table>

</body>
</html>
