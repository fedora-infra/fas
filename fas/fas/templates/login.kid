<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'master.kid'">
  <head>
    <title>Login to the Fedora Accounts System</title>
  </head>
  <style type="text/css">
    #content ul
    {
      list-style: square;
      margin: 1ex 3ex;
    }
  </style>
  <body>
    <h2>Login</h2>
    <p>${message}</p>
    <form action="${previous_url}" method="POST">
      <ul>
        <li><label for="user_name">User Name:</label> <input type="text" id="user_name" name="user_name" /></li>
        <li><label for="password">Password:</label> <input type="password" id="password" name="password" /></li>
        <li>
        <input type="submit" name="login" value="Login" />
        <input py:if="forward_url" type="hidden" name="forward_url" value="${tg.url(forward_url)}" />
        <input py:for="name,value in original_parameters.items()" type="hidden" name="${name}" value="${value}" />
        </li>
      </ul>
    </form>
    <ul>
      <li><a href="resetPassword">Forgot Password?</a></li>
      <li><a href="signUp">Sign Up</a></li>
    </ul>
  </body>
</html>
