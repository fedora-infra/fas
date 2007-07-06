<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">

<head>
 <style type="text/css">
@import "/static/css/fas.css";

 </style>
</head>
<body>

<script src="/fas/static/javascript/forms.js" type="text/javascript"></script>
<!--
<form action='newAccountSubmit' method='post'>
    <table>
        <tr><td>username:</td><td><input type='text' name='cn'/></td></tr>
        <tr><td>Real Name:</td><td><input type='text' name='givenName'/></td></tr>
        <tr><td>email:</td><td><input type='text' name='mail'/></td></tr>
        <tr><td>Telephone Number:</td><td><input type='text' name='telephoneNumber'/></td></tr>
        <tr><td>Postal Address:</td><td><textarea name='postalAddress'></textarea></td></tr>
        <tr><td><input type='submit'/></td><td></td></tr>
    </table>
</form>-->

${form(action='newAccountSubmit', method='post')}
</body>
</html>
