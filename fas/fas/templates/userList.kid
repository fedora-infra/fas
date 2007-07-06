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
    Search <input type='text' name='search' value='${search}' size='15'/> (Ex: "mmcg*")
</form>

<table>
    <tr>
        <td width='10' align='center' py:for="letter in 'abcdefghijklmnopqrstuvwxyz'.upper()">
            <a href='?search=${letter}*'>${letter}</a>
        </td>
        <td><a href='?search=*'>All</a></td>
    </tr>
</table>
<table id='sortable_table' class='datagrid'>
    <thead>
        <tr><th mochi:format="str">Username</th></tr>
    </thead>
    <tr py:for="item in printList">
        <td>${item} <a href="editAccount?userName=${item}">(edit)</a></td>
    </tr>
</table>

</body>
</html>
