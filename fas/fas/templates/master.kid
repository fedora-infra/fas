<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python import sitetemplate ?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="sitetemplate">

<head py:match="item.tag=='{http://www.w3.org/1999/xhtml}head'" py:attrs="item.items()">
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" py:replace="''"/>
    <title py:replace="''">Your title goes here</title>
    <meta py:replace="item[:]"/>
    <style type="text/css">
        #pageLogin
        {
            font-size: 10px;
            font-family: verdana;
            text-align: right;
        }
    </style>
    <style type="text/css" media="screen">
@import "/fas/static/css/style.css";
</style>
    <script src="/fas/static/javascript/MochiKit.js" type="text/javascript"></script>
    <script src="/fas/static/javascript/New.js" type="text/javascript"></script>
</head>

<body py:match="item.tag=='{http://www.w3.org/1999/xhtml}body'" py:attrs="item.items()">
    <div id="wrapper">
      <div id="head">
        <h1><a href="/">Fedora</a></h1>
        <div py:if="tg_flash" class="flash" id='flashMessage'>
            ${tg_flash} <a href='' onClick="squish('flashMessage'); return false;">(hide)</a>
        </div>
        <div id="searchbox">
          <form action="" method="get">
            <label for="q">Search:</label>
            <input type="text" name="q" id="q"/>
            <input type="submit" value="Search"/>
          </form>
        </div>
      </div>
      <div id="topnav">
        <ul>
          <li class="first"><a href="http://fedoraproject.org/">Learn about Fedora</a></li>
          <li><a href="http://fedoraproject.org/get-fedora.html">Download Fedora</a></li>
          <li><a href="http://fedoraproject.org/wiki/">Projects</a></li>
          <li><a href="http://fedoraproject.org/join-fedora.html">Join Fedora</a></li>
          <li><a href="/">Communicate</a></li>
          <li><a href="http://docs.fedoraproject.org/">Help/Documentation</a></li>
        </ul>
      </div>
      <div id="infobar">
        <div id="authstatus">
          <span py:if="not tg.identity.anonymous">
            <strong>Logged in: </strong>${tg.identity.user.user_name}.
          </span>
        </div>
        <div id="control">
          <ul>
            <li py:if="not tg.identity.anonymous"><a href="editAccount">My Account</a></li>
            <li py:if="not tg.identity.anonymous"><a href="logout">Log Out</a></li>
            <li py:if="tg.identity.anonymous"><a href="login">Log In</a></li>
          </ul>
        </div>
      </div>
      <div id="main">
        <div id="sidebar">
          <ul>
            <li class="first"><a href="listGroup">Group List</a></li>
            <li py:if="'accounts' in tg.identity.groups"><a href="listUser">User List</a></li>
            <li><a href="http://fedoraproject.org/wiki/FWN/LatestIssue">News</a></li>
            <li><a href="listGroup?search=A*">Apply For a new Group</a></li>
          </ul>
        </div>
<!--      </div>
    </div>-->









<!--    <div py:if="tg.config('identity.on',False) and not 'logging_in' in locals()"
        id="pageLogin">
        <span py:if="tg.identity.anonymous">
            <a href="${tg.url('/login')}">Login</a>
        </span>
        <span py:if="not tg.identity.anonymous">
            Welcome ${tg.identity.user.user_name}.
            <a href="${tg.url('/logout')}">Logout</a>
        </span>
    </div>-->
<!--    <div id="header">&nbsp;</div>
    <div id="main_content">-->
    <div id='content'>
        <div class="help" id='helpMessageMain' style='display: none'>
            <div id='helpMessage'>
                Help!  What is interesting about this piece of help is that it's really long.  I wonder if it will word wrap?  That is so f'ing beautiful.  You have NO idea.
            </div>
            <a href='' onClick="squish('helpMessageMain'); return false;">(hide)</a>

            <script src="/fas/static/javascript/forms.js" type="text/javascript"></script>
        </div>


      <!--<div py:if="tg_flash" class="flash" id='flashMessage'>
        ${tg_flash} <a href='' onClick="squish('flashMessage'); return false;">(hide)</a>
      </div>-->

    <div py:replace="[item.text]+item[:]"/>

	<!-- End of content -->
	</div>
  </div> <!-- End main -->
<div id="footer"> <img src="/static/images/under_the_hood_blue.png" alt="TurboGears under the hood" />
  <p>TurboGears is a open source front-to-back web development
    framework written in Python</p>
  <p>Copyright &copy; 2006 Kevin Dangoor</p>
</div>
</div> <!-- End wrapper -->
</body>
</html>
