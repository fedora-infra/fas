<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'master.kid'">
  <head>
    <title>Users List</title>
  </head>
  <body>
    <h2>List (${search})</h2>
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
    <table>
      <thead>
        <tr>
          <th>Username</th>
          <th>Account Status</th>
        </tr>
      </thead>
      <tbody>
        <?python
        users.sort()
        ?>
        <tr py:for="user in users">
          <td><a href="editAccount?userName=${user}">${user}</a></td>
          <td>
            <span py:if="claDone[user]" class="approved"> Done</span>
            <span py:if="not claDone[user]" class="unapproved"> Done</span>
          </td>
        </tr>
      </tbody>
    </table>
  </body>
</html>
