<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'"
    xmlns:mochi="MyUniqueMochiUri">
<head>
 <style type="text/css">
@import "/fas/static/css/fas.css";
@import '/fas/static/css/sortable_tables.css';
 </style>
</head>
<body>

<script src="/fas/static/javascript/sortable_tables.js" type="text/javascript"></script>

<h2 py:if="'userID' in builds.userLink" id="your-account-header"><img src="static/images/header-icon_account.png" /> Recent Builds <a href='${builds.userLink}'>(Koji)</a></h2>
<table py:if="'userID' in builds.userLink" id='sortable_table' class='datagrid'>
    <thead>
        <tr><th mochi:format='str'>Build</th><th mochi:format='date'>Build Date</th></tr>
    </thead>
    <!--<tr><td>Koji</td><td><a href='${builds.userLink}'>Build Info</a></td></tr>-->
    <tr py:for="build in builds.builds">
        <td>
            <font py:if="'complete' in builds.builds[build]['title']" color='green'>${builds.builds[build]['title']}</font>
            <font py:if="'failed' in builds.builds[build]['title']" color='red'>${builds.builds[build]['title']}</font>
            <a href="${build}">(build)</a>
        </td>
        <td>${builds.builds[build]['pubDate']}</td>
    </tr>
</table>

</body>
</html>
