<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">

<head>
 <style type="text/css">
@import "/static/css/fas.css";
@import "/static/css/draggable.css";

 </style>
</head>
<body>

<div class='draggable white' style="left: 10px; display: none" id='help'>close</div>
<script src="/fas/static/javascript/forms.js" type="text/javascript"></script>
<script src="/fas/static/javascript/draggable.js" type="text/javascript"></script>
<h2 id="your-account-header"><img src="static/images/header-icon_account.png" />Your Fedora Account</h2>

<table class="account-info" id="your-account-basic-info">
 <tbody>
    <tr>
        <td>Account Name <a href='' onClick="displayHelp('cn'); return false;">(?)</a>:</td>
        <td>${user.cn}</td>
    </tr> 
    <tr>
        <td>Real Name <a href='' onClick="displayHelp('givenName'); return false;">(?)</a>:</td>
        <td>
            <div id='givenName'>${user.givenName} <a href="" onclick="formEdit('givenName'); return false;">(edit)</a></div>
            <div id='givenNameForm' style='display: none'>
                <form method='post' action='editUserAttribute'>
                    <input type='hidden' name='userName' value='${user.cn}'/>
                    <input type='hidden' name='attribute' value='givenName'/>
                    <input type='text' name='value' value='${user.givenName}'/>
                    <a href='' onclick="cancelEdit('givenName'); return false;">(cancel)</a>
                </form>
            </div>
        </td>
    </tr>
    <tr>
        <td>Email <a href='' onClick="displayHelp('mail'); return false;">(?)</a>:</td>
        <td>
            <div id='mail'>${user.mail} <a href='' onclick="formEdit('mail'); return false;">(edit)</a></div>
            <div id='mailForm' style='display: none'>
                <form method='post' action='editUserAttribute'>
                    <input type='hidden' name='userName' value='${user.cn}'/>
                    <input type='hidden' name='attribute' value='mail'/>
                    <input type='text' name='value' value='${user.mail}'/>
                    <a href='editAccount' onclick="cancelEdit('mail'); return false;">(cancel)</a>
                </form>
            </div>
        </td>
    </tr>
    <tr>
        <td>Bugzilla Email <a href='' onClick="displayHelp('fedoraPersonBugzillaMail'); return false;">(?)</a>:</td>
        <td>
            <div id='fedoraPersonBugzillaMail'>${user.fedoraPersonBugzillaMail} <a href='' onclick="formEdit('fedoraPersonBugzillaMail'); return false;">(edit)</a></div>
            <div id='fedoraPersonBugzillaMailForm' style='display: none'>
                <form method='post' action='editUserAttribute'>
                    <input type='hidden' name='userName' value='${user.cn}'/>
                    <input type='hidden' name='attribute' value='fedoraPersonBugzillaMail'/>
                    <input type='text' name='value' value='${user.fedoraPersonBugzillaMail}'/>
                    <a href='editAccount' onclick="cancelEdit('fedoraPersonBugzillaMail'); return false;">(cancel)</a>
                </form>
            </div>
        </td>
    </tr>
    <tr>
        <td>IRC Nick <a href='' onClick="displayHelp('fedoraPersonIrcNick'); return false;">(?)</a>:</td>
        <td>
            <div id='fedoraPersonIrcNick'>${user.fedoraPersonIrcNick} <a href='' onclick="formEdit('fedoraPersonIrcNick'); return false;">(edit)</a></div>
            <div id='fedoraPersonIrcNickForm' style='display: none'>
                <form method='post' action='editUserAttribute'>
                    <input type='hidden' name='userName' value='${user.cn}'/>
                    <input type='hidden' name='attribute' value='fedoraPersonIrcNick'/>
                    <input type='text' name='value' value='${user.fedoraPersonIrcNick}'/>
                    <a href='editAccount' onclick="cancelEdit('fedoraPersonIrcNick'); return false;">(cancel)</a>
                </form>
            </div>
        </td>
    </tr>

    <tr>
        <td>PGP Key <a href='' onClick="displayHelp('fedoraPersonKeyId'); return false;">(?)</a>:</td>
        <td>
            <div id='fedoraPersonKeyId'>${user.fedoraPersonKeyId} <a href='' onclick="formEdit('fedoraPersonKeyId'); return false;">(edit)</a></div>
            <div id='fedoraPersonKeyIdForm' style='display: none'>
                <form method='post' action='editUserAttribute'>
                    <input type='hidden' name='userName' value='${user.cn}'/>
                    <input type='hidden' name='attribute' value='fedoraPersonKeyId'/>
                    <input type='text' name='value' value='${user.fedoraPersonKeyId}'/>
                    <a href='editAccount' onclick="cancelEdit('fedoraPersonKeyId'); return false;">(cancel)</a>
                </form>
            </div>
        </td>
    </tr>

    <tr>
        <td>Telephone Number <a href='' onClick="displayHelp('telephoneNumber'); return false;">(?)</a>:</td>
        <td>
            <div id='telephoneNumber'>${user.telephoneNumber} <a href='' onclick="formEdit('telephoneNumber'); return false;">(edit)</a></div>
            <div id='telephoneNumberForm' style='display: none'>
                <form method='post' action='editUserAttribute'>
                    <input type='hidden' name='userName' value='${user.cn}'/>
                    <input type='hidden' name='attribute' value='telephoneNumber'/>
                    <input type='text' name='value' value='${user.telephoneNumber}'/>
                    <a href='editAccount' onclick="cancelEdit('telephoneNumber'); return false;">(cancel)</a>
                </form>
            </div>
        </td>
    </tr>

    <tr>
        <td>Postal Address <a href='' onClick="displayHelp('postalAddress'); return false;">(?)</a>:</td>
        <td>
            <div id='postalAddress'><pre>${user.postalAddress}</pre><a href='' onclick="formEdit('postalAddress'); return false;">(edit)</a></div>
            <div id='postalAddressForm' style='display: none'>
                <form method='post' action='editUserAttribute'>
                    <input type='hidden' name='userName' value='${user.cn}'/>
                    <input type='hidden' name='attribute' value='postalAddress'/>
                    <textarea name='value'>${user.postalAddress}</textarea>
                    <input type='submit' value='submit'/>
                    <a href='editAccount' onclick="cancelEdit('postalAddress'); return false;">(cancel)</a>
                </form>
            </div>
        </td>
    </tr>

    <tr>
        <td>Description <a href='' onClick="displayHelp('description'); return false;">(?)</a>:</td>
        <td>
            <div id='description'><pre>${user.description}</pre><a href='' onclick="formEdit('description'); return false;">(edit)</a></div>
            <div id='descriptionForm' style='display: none'>
                <form method='post' action='editUserAttribute'>
                    <input type='hidden' name='userName' value='${user.cn}'/>
                    <input type='hidden' name='attribute' value='description'/>
                    <textarea name='value'>${user.description}</textarea>
                    <input type='submit' value='submit'/>
                    <a href='editAccount' onclick="cancelEdit('description'); return false;">(cancel)</a>
                </form>
            </div>
        </td>
    </tr>

    <tr>
        <td>Password <a href='' onClick="displayHelp('password'); return false;">(?)</a>: </td>
        <td><img src="static/images/status_approved.png" />
       Valid <span class="edit-button"><a href="resetPassword">(change)</a></span>
        </td>
    </tr>
    <tr>
        <td>Account Status <a href='' onClick="displayHelp('accountStatus'); return false;">(?)</a>:</td>
        <td><img src="static/images/status_approved.png" />
            Approved, Active <span class="edit-button"><a href="#">(deactivate)</a></span>
        </td>
    </tr>
    <tr>
	<td>CLA <a href='' onClick="displayHelp('cla'); return false;">(?)</a>:</td>
	<td py:if='claDone'><img src='static/images/status_approved.png'/> Done <a href="#">(?)</a></td>
	<td py:if='not claDone'><img src='static/images/status_incomplete.png'/> Not Done <a href="#">(?)</a></td>
    </tr>
<!--    <tr>
        <td>Description:</td>
        <td>
            <div id="description_form" style="display: none"><form method='post' action='editUserAttribute'>
                <input type='hidden' name='attribute' value='description'/>
                <textarea name='value'>${user.description}</textarea>
                <input type='submit' value='submit'/>
                <a href='editAccount'>(Cancel)</a>
            </form></div>
            <div id='description_actual'>
                <pre>${user.description}</pre>
            </div>
            <a href='#' onClick="toggle('description_form'); return false;">Edit</a>
        </td>
        <td py:if='not action == "description"'><pre>${user.description}</pre>
            <span class="edit-button">
                <a href="${tg.url('', action='description')}">(edit)</a>
            </span>-
        </td>
    </tr>-->

 </tbody>
</table>

<h2 id="your-account-header-roles">Your Roles</h2>

<h2 py:if="groupsPending">Pending</h2>
<div id='gpShow' style='display: none'><a href='' onclick="blindDown('groupsPending'); fade('gpShow'); appear('gpHide'); return false;">Show</a></div>
<div id='gpHide'><a href='' onclick="blindUp('groupsPending'); fade('gpHide'); appear('gpShow'); return false;">Hide</a></div>
<div id='groupsPending'>
    <ul class="tool-links">
        <li py:for='group in groupsPending'><img src="static/images/status_incomplete.png"/> ${groupsPending[group].cn} <a href="${tg.url('editGroup', groupName=groupsPending[group].cn)}">(edit)</a></li>
    </ul>
</div>

<h2 py:if="groups">Approved</h2>
<div id='gShow'><a href='' onclick="blindDown('groups'); fade('gShow'); appear('gHide'); return false;">Show</a></div>
<div id='gHide' style='display: none'><a href='' onclick="blindUp('groups'); fade('gHide'); appear('gShow'); return false;">Hide</a></div>
<div id='groups' style='display: none'>
    <ul class="tool-links">
        <li py:for='group in groups'><img src="static/images/status_approved.png"/> ${groups[group].cn} <a href="${tg.url('editGroup', groupName=groups[group].cn)}">(edit)</a></li>
    </ul>
</div>
<h2>Misc</h2>

<table class="account-info your-account-role-info">
 <tbody>
  <tr>
   <td>Status:</td>
   <td><img src="static/images/status_approved.png" />
       Approved, Active <a href="#">(edit)</a>
   </td>
  </tr><tr>
   <td>Tools:</td>
   <td>
    <ul class="tool-links">
     <li><a href="listGroup">Apply for new group ...</a></li>
     <li><a href="invite">Invite a New Member ...</a></li>
     <li><a href="#">View All Pending Membership Requests ...</a></li>
    </ul>
   </td>
  </tr><tr>
   <td>Queue:</td>
   <td>
    <ul class="queue-links">
     <li><a href="#">Chewbacca D. Wookiee requests approval to join project as <strong>user</strong> ...</a></li>
     <li><a href="#">Gaius Baltar request approval to upgrade from <strong>user</strong> to <strong>administrator</strong> ...</a></li>
     <li><a href="#">Leia Organa requests approval to upgrade from <strong>user</strong> to <strong>sponsor</strong> ...</a></li>
    </ul>
   </td>
  </tr>
 </tbody>
</table>

</body>
</html>
