<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">

<head>
 <style type="text/css">
@import "/fas/static/css/fas.css";
 </style>
</head>
<body>
<span py:if="tg.identity.anonymous">
    <form method='post'>
        Username: <input type='text' name='userName'/><br/>
        Primary Email: <input type='password' name='mail'/><br/>
        <input type='submit'/>
    </form>
</span>
<span py:if=" not tg.identity.anonymous">
    <form method='post'>
        New password for ${tg.identity.user.user_name}<br/>
        New Password: <input type='password' name='password'/><br/>
        Verify Password: <input type='password' name='passwordCheck'/>
        <input type='submit'/>
    </form>
</span>

</body>
</html>
