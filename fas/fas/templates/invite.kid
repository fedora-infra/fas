<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">

<head>
 <style type="text/css">
@import "/static/css/fas.css";
 </style>
</head>
<body>

<h1>Invite a new community member!</h1>

<form method='POST'>
    To email: <input type='text' value='' name='target'/><br/>
    From: ${user.mail}<br/>
    Subject: Invitation to join the Fedora Team!<br/>
    Message: Please come up with a better more inviting message.<br/>
<pre>
${user.givenName} &le;<a href='mailto: ${user.mail}'>${user.mail}</a>&ge; has invited you to join the Fedora
Project!  We are a community of users and developers who produce a
complete operating system from entirely free and open source software
(FOSS).  ${user.givenName} thinks that you have knowledge and skills
that make you a great fit for the Fedora community, and that you might
be interested in contributing.

How could you team up with the Fedora community to use and develop your
skills?  Check out http://fedoraproject.org/wiki/Join for some ideas.
Our community is more than just software developers -- we also have a
place for you whether you're an artist, a web site builder, a writer, or
a people person.  You'll grow and learn as you work on a team with other
very smart and talented people.

Fedora and FOSS are changing the world -- come be a part of it!
</pre>
    <input type='submit'/>
</form>
</body>

</html>
