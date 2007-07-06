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
<h1>List (${search})</h1>

<form method='GET'>
    Search <input type='text' value='${search}' name='search' size='15'/> (Ex: "cvs*")
</form>

<table>
    <tr>
        <td width='10' align='center' py:for="letter in 'abcdefghijklmnopqrstuvwxyz'.upper()">
            <a href='?search=${letter}*'>${letter}</a>
        </td>
        <td><a href='?search=*'>All</a></td>
    </tr>
</table>
<table py:if="groups" id='sortable_table' class='datagrid'>
    <thead>
    <tr><th mochi:format="str">Group</th><th mochi:format='istr'>Status</th></tr>
    </thead>
    <tr py:for="group in groups">
        <td>${groups[group].cn} <a href="editGroup?groupName=${groups[group].cn}">(edit)</a>
            <a href='' onClick="displayHelp('info'); return false;">(info)</a></td>
        <td align='center'>
            <a py:if="groups[group].cn in myGroups" href="${tg.url('editGroup', groupName=groups[group].cn)}"><img src="static/images/status_approved.png" border='0'/></a>
            <a py:if="groups[group].cn not in myGroups" href="${tg.url('editGroup', groupName=groups[group].cn)}"><img src="static/images/status_incomplete.png" border='0'/></a>
        </td>
    </tr>
</table>

</body>
</html>
