<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="'master.kid'">
  <head>
    <title>Welcome to FAS2</title>
    <style type="text/css">
      #content ul
      {
        list-style: square;
        margin: 1ex 3ex;
      }
    </style>
  </head>
  <body>
    <p>
    Welcome to the Fedora Accounts System 2.  This system is not yet live so feel free to play around.  Just don't expect it to work.
    </p>
    <ul>
      <li><a href="${tg.url('login')}">Log In</a></li>
      <li><a href="${tg.url('signUp')}">New Account</a></li>
      <li><a href="http://fedoraproject.org/wiki/Join">Why Join?</a></li>
    </ul>
  </body>
</html>
