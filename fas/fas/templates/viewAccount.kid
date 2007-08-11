<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'master.kid'">
  <head>
    <title>View Account</title>
  </head>
  <body>
    <h2 class="account" py:if="personal">Your Fedora Account</h2>
    <h2 class="account" py:if="not personal">${user.givenName}'s Fedora Account</h2>
    <h3>Account Details <a href="${tg.url('/editAccount', userName=user.cn)}" py:if="personal or admin">(edit)</a></h3>
    <div class="userbox">
      <dl>
        <dt>Account Name</dt><dd>${user.cn}</dd>
        <dt>Real Name</dt><dd>${user.givenName}</dd>
        <dt>Email</dt><dd>${user.mail}</dd>
        <dt>Bugzilla Email</dt><dd>${user.fedoraPersonBugzillaMail}</dd>
        <dt>IRC Nick</dt><dd>${user.fedoraPersonIrcNick}</dd>
        <dt>PGP Key</dt><dd>${user.fedoraPersonKeyId}</dd>
        <dt>Telephone Number</dt><dd>${user.telephoneNumber}</dd>
        <dt>Postal Address</dt><dd>${user.postalAddress}</dd>
        <dt>Description</dt><dd>${user.description}</dd>
        <dt>Password</dt><dd><span class="approved">Valid</span> <a href="${tg.url('/resetPassword')}" py:if="personal">(change)</a></dd>
        <dt>Account Status</dt><dd><span class="approved">Approved</span>, Active</dd>
        <dt>CLA</dt><dd><span py:if="claDone" class="approved">Done</span><span py:if="not claDone" class="unapproved"> Not Done</span></dd>
      </dl>
    </div>
    <h3 py:if="personal">Your Roles</h3>
    <h3 py:if="not personal">${user.givenName}'s Roles</h3>
    <?python
    keys = groups.keys()
    keys.sort()
    keysPending = groupsPending.keys()
    keysPending.sort()
    ?>
    <ul class="roleslist">
      <li py:for="group in map(groups.get, keys)"><span class="team approved">${groupdata[group.cn].fedoraGroupDesc} (${group.cn})</span></li>
      <li py:for="group in map(groupsPending.get, keysPending)"><span class="team unapproved">${groupdata[group.cn].fedoraGroupDesc} (${group.cn})</span></li>
    </ul>
    <ul class="actions" py:if="personal">
      <li><a href="/">(Join another project)</a></li>
      <li><a href="/">(Create a new project)</a></li>
    </ul>
    <ul id="rolespanel" py:if="personal">
      <li py:for="group in map(groups.get, keys)" class="role">
      <h4>${groupdata[group.cn].fedoraGroupDesc}</h4>, ${group.fedoraRoleType}
      <dl>
        <dt>Status:</dt>
        <dd>
        <span class="approved">Approved</span>, Active
        </dd>
        <dt>Tools:</dt>
        <dd>
        <ul class="tools">
          <li><a href="/">Invite a New Member...</a></li>
          <li py:if="group.fedoraRoleType.lower() in ('administrator', 'sponsor')"><a href="${tg.url('/viewGroup', groupName=group.cn)}">View All Pending Group Membership Requests...</a></li>
          <li><a href="${tg.url('/viewGroup', groupName=group.cn)}">Manage Group Membership...</a></li>
          <li py:if="group.fedoraRoleType.lower() == 'administrator'"><a href="${tg.url('/editGroup', groupName=group.cn)}">Manage Group Details...</a></li>
        </ul>
        </dd>
        <div py:if="group.fedoraRoleType.lower() in ('administrator', 'sponsor')" py:strip="">
          <dt>Queue:</dt>
          <dd>
          <ul class="queue">
            <li><a href="/">Chewbacca D. Wookiee requests approval to join project as a <strong>user</strong></a></li>
            <li><a href="/">Gaius Baltar requests approval to upgrade from <strong>user</strong> to <strong>sponsor</strong></a></li>
            <li><a href="/">Leia Organa requests approval to upgrade from <strong>user</strong> to <strong>administrator</strong></a></li>
          </ul>
          </dd>
        </div>
      </dl>
      </li>
    </ul>
  </body>
</html>
