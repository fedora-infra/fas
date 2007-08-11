<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
  py:extends="'master.kid'">
  <head>
    <title>Edit Group</title>
  </head>
  <body>
    <h2>${group.fedoraGroupDesc} (${group.cn})</h2>
    <h3>
      My Status: 
      <span py:if="me.fedoraRoleStatus.lower() == 'approved'" class="approved">Approved</span>
      <span py:if="me.fedoraRoleStatus.lower() == 'unapproved'" class="unapproved">Unapproved</span>
      <span py:if="'Not a Member' in me.fedoraRoleStatus">Not a Member</span>
    </h3>
    <form py:if="'Not a Member' in me.fedoraRoleStatus" action="${tg.url('/applyForGroup')}">
      <div>
        <input type="hidden" name="groupName" value="${group.cn}" />
        <input type="text" name="requestField" value="Please let me join.." />
        <input type="submit" name="action" value="Join" />
      </div>
    </form>
    <a py:if="'Not a Member' not in me.fedoraRoleStatus" href="${tg.url('/applyForGroup', groupName=group.cn, action='Remove')}">Remove me</a>
    <h3>Group Details <a href="${tg.url('editGroup', groupName=group.cn)}">(edit)</a></h3>
    <div class="userbox">
      <dl>
        <dt>Name:</dt><dd>${group.cn}</dd>
        <dt>Description:</dt><dd>${group.fedoraGroupDesc}</dd>
        <dt>Owner:</dt><dd>${group.fedoraGroupOwner}</dd>
        <dt>Type:</dt><dd>${group.fedoraGroupType}</dd>
        <dt>Needs Sponsor:</dt><dd>
        <span py:if="group.fedoraGroupNeedsSponsor == 'TRUE'" py:strip="">Yes</span>
        <span py:if="group.fedoraGroupNeedsSponsor == 'FALSE'" py:strip="">No</span>
        </dd>
        <dt>Self Removal</dt><dd>
        <span py:if="group.fedoraGroupUserCanRemove == 'TRUE'" py:strip="">Yes</span>
        <span py:if="group.fedoraGroupUserCanRemove == 'FALSE'" py:strip="">No</span>
        </dd>
        <dt>Join Message:</dt><dd>${group.fedoraGroupJoinMsg}</dd>
      </dl>
    </div>
    <h3 py:if='me.fedoraRoleStatus == "approved"'>Invite</h3>
    <span py:if='me.fedoraRoleStatus == "approved"'>${searchUserForm(action='modifyGroup', value=value, method='get')}</span>
    <h3>Members</h3>
    <table>
      <thead>
        <tr>
          <th>Username</th>
          <th>Sponsor</th>
          <th>Date Added</th>
          <th>Date Approved</th>
          <th>Approval</th>
          <th>Role Type</th>
          <th py:if='me.fedoraRoleType == "administrator" or me.fedoraRoleType == "sponsor"'>Action</th>
        </tr>
      </thead>
      <tr py:for="user in groups">
        <td><a href="${tg.url('viewAccount/%s' % user)}">${user}</a></td>
        <td py:if='not(groups[user].fedoraRoleSponsor ==  "None")'><a href="%{tg.url('viewAccount/%s' % groups[user].fedoraRoleSponsor)}">${groups[user].fedoraRoleSponsor}</a></td>
        <td py:if='groups[user].fedoraRoleSponsor == "None"'>${groups[user].fedoraRoleSponsor}</td>
        <td>${groups[user].fedoraRoleCreationDate}</td>
        <td>${groups[user].fedoraRoleApprovalDate}</td>
        <td>${groups[user].fedoraRoleStatus}</td>
        <td>${groups[user].fedoraRoleType}</td>
        <!--<td>${groups[user].fedoraRoleDomain}</td>-->
        <!-- This section includes all action items -->
        <td py:if='me.fedoraRoleType == "administrator"'>
          <a py:if="group.fedoraGroupNeedsSponsor.upper() == 'TRUE'" href="${tg.url('/modifyGroup', groupName=groups[user].cn, userName=user, action='sponsor')}">Sponsor</a>
          <a py:if="not group.fedoraGroupNeedsSponsor.upper() == 'TRUE' and groups[user].fedoraRoleStatus.lower() != 'approved'" href="${tg.url('/modifyGroup', groupName=groups[user].cn, userName=user, action='sponsor')}">Approve</a>
          <a href="${tg.url('/modifyGroup', groupName=groups[user].cn, userName=user, action='remove')}">Delete</a>
          <a href="${tg.url('/modifyGroup', groupName=groups[user].cn, userName=user, action='upgrade')}">Upgrade</a>
          <a href="${tg.url('/modifyGroup', groupName=groups[user].cn, userName=user, action='downgrade')}">Downgrade</a> Suspend
        </td>
        <td py:if='me.fedoraRoleType == "sponsor" and not groups[user].fedoraRoleType == "administrator"'>
          <a href="${tg.url('/modifyGroup', groupName=groups[user].cn, userName=user, action='sponsor')}" py:if="group.fedoraGroupNeedsSponsor.upper() == 'TRUE'">Sponsor</a>
          <a href="${tg.url('/modifyGroup', groupName=groups[user].cn, userName=user, action='sponsor')}" py:if="not group.fedoraGroupNeedsSponsor.upper() == 'TRUE'">Approve</a>
          <a href="${tg.url('/modifyGroup', groupName=groups[user].cn, userName=user, action='remove')}">Delete</a>
          <a py:if='groups[user].fedoraRoleType' href="${tg.url('/modifyGroup', groupName=groups[user].cn, userName=user, action='upgrade')}">Upgrade</a>
          <a href="${tg.url('/modifyGroup', groupName=groups[user].cn, userName=user, action='downgrade')}">Downgrade</a> Suspend
          <div py:if="'not' in '%s' % tg_flash and user in '%s' % tg_flash"> -- Error!</div><!-- Clean this up -->
        </td>
      </tr>
    </table>
  </body>
</html>
