<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#">

<head>
 <style type="text/css">
@import "/static/css/fas.css";
 </style>
</head>
<body>
    <div py:if="tg_flash" class="flash" py:content="tg_flash"></div>
    <form method='post'>
        <!-- This needs to be fixed before going live -->
        <input type='hidden' name='attribute' value='${attribute}'/>
        <input type='hidden' name='update' value='True'/>
        <input type='hidden' name='userName' value='${userName}' />
        <input type='text' name='value' value='${value}'/>
    </form>
</body>
</html>
