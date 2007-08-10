<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
  py:extends="'master.kid'">
  <head>
    <title>Groups List</title>
  </head>
  <body>
    <h2>List (${search})</h2>
    <h3>Search Groups</h3>
    <form method="GET">
      <p>"*" is a wildcard (Ex: "cvs*")</p>
      <div>
        <input type="text" value="${search}" name="search" size="15 "/>
        <input type="submit" value="Search" />
      </div>
    </form>
    <h3>Results</h3>
    <ul class="letters">
      <li py:for="letter in 'abcdefghijklmnopqrstuvwxyz'.upper()"><a href="?search=${letter}*">${letter}</a></li>
      <li><a href="?search=*">All</a></li>
    </ul>

    <table py:if="groups">
      <thead>
        <tr><th>Group</th><th>Description</th><th>Status</th></tr>
      </thead>
      <tbody>
        <?python
        keys = groups.keys()
        keys.sort()
        ?>
        <tr py:for="group in map(groups.get, keys)">
          <td><a href="${tg.url('viewGroup', groupName=group.cn)}">${group.cn}</a></td>
          <td>${group.fedoraGroupDesc}</td>
          <td>
            <a py:if="group.cn in myGroups" href="${tg.url('viewGroup', groupName=group.cn)}">
              <span class="approved" py:if="myGroups[group.cn].fedoraRoleStatus.lower() == 'approved'">Approved</span>
              <span class="unapproved" py:if="myGroups[group.cn].fedoraRoleStatus.lower() == 'unapproved'">Unapproved</span>
            </a>
            <a py:if="group.cn not in myGroups" href="${tg.url('viewGroup', groupName=group.cn)}"><span>Not a Member</span></a>
          </td>
        </tr>
      </tbody>
    </table>
  </body>
</html>
