<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'master.kid'">
  <head>
    <title>Reset Password</title>
  </head>
  <body>
    <h2>Reset Password</h2>
    <div py:if="tg.identity.anonymous" py:strip="">
      <form method="post">
        <ul>
          <li><label for="userName">Username:</label> <input type="text" id="userName" name="userName" /></li>
          <li><label for="mail">Primary Email:</label> <input type="password" id="mail" name="mail" /></li>
          <li><input type="submit" value="Reset Password" /></li>
        </ul>
      </form>
    </div>
    <div py:if="not tg.identity.anonymous" py:strip="">
      <p>
      New password for ${tg.identity.user.user_name}
      </p>
      <form method="post">
        <ul>
          <li><label for="password">New Password:</label> <input type="password" name="password" /></li>
          <li><label for="password">Verify Password:</label> <input type="password" name="passwordCheck" /></li>
          <li><input type="submit" /></li>
        </ul>
      </form>
    </div>
  </body>
</html>
