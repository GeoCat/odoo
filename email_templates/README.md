# GeoCat Email Templates for Odoo

This folder contains HTML email templates used by various Odoo modules.

These templates are **not** part of the GeoCat Customization module: they will not be deployed automatically,
but they need to be **manually** set in the Odoo Settings (search for `Email Templates`).

## Different kinds of email templates

In Odoo, 2 kinds of email templates exist:

- _Email layout templates_: these contain the outer shell of the email, with the header, footer, and general layout/styling.  
  These are actually QWeb `<template>` views, which are overridden by the GeoCat Customization module using `<xpath>` expressions.  
  See `geocat/data/mail_templates_email_layouts.xml` for all overrides.
- _Email data templates_: these contain the layout and placeholders for the actual content of the email, e.g. the body text.  
  These templates are stored in `<record>` objects, which are not (!) overridden by the GeoCat Customization module.
  They often cannot be (easily) overridden either, because some have the `noupdate="1"` attribute set.  

:warning: The folder you are currently in only contains the HTML for these _email data templates_, but not the other settings (like subject, recipient, etc.) stored in the `<record>` (and database).

Odoo modules usually define one or more data templates (in `mail_template_data.xml`), which are then populated at runtime and wrapped in a layout template, before they are sent out.

In the Odoo settings, both can be configured manually as well, although you need administrative privileges, and for the layout templates,
you even need to enable the developer mode to see them:

![Email Settings](img/email_settings.png)

Also, note that there are 2 layout templates: a regular one (`mail_notification_layout` - which is the one you see when clicking "Update Mail Layout"), and a simplified one.
The latter can only be found in developer mode: go to `Settings` -> `Technical` -> `User Interface` -> `Views` and search for `mail_notification_light`.  
The simplified layout currently has been changed to look (almost) exactly like the standard one: there is no visible difference, except for the HTML structure.

:warning: WARNING :warning:  
Odoo actually allows sending emails without using any wrapper templates at all. In fact, several modules (Subscription, Timesheets, portal invite) render a data template record and send it as-is,
without specifying a layout template.  
To make this more consistent, the GeoCat Customization module overrides methods of the `MailTemplate` and `MailComposer` models, so that it always sets the `mail_notification_layout` template if missing.
This means that in order to avoid "duplicate" layout blocks, all the layout stuff (headers, footers, etc.) has to be removed from the data templates in the `Email Templates` records of Odoo!


## Why do we do this?

We have a couple of good reasons why we want to override the email templates in Odoo:

1. The default Odoo email templates look like shit. ;)
2. They often contain information that we don't need or wish to hide, would like to see rephrased, or moved to a different section.  
   For example, the data templates contain a user signature, but we want to move that to the layout template and make it more general (e.g. "Best regard, The GeoCat Team").
3. Only the layout templates (views) respect the `Header` and `Button` color settings (linked to the active user company), 
   but many of the data templates (records) have "hard coded" Odoo branding (purple colors) in them.
4. Most email templates contain a "Powered by Odoo" footer, which we don't want to see.

As mentioned before, we can only override the layout templates, but the data template record can't all be overridden (`<odoo noupdate="1">`), which means that we would have to use a hack to get them replaced automatically.

For now this means that we will have to manually update each record in the Odoo Settings, which is a laborious activity.
However, the alternative (defining record overrides in the GeoCat module for all Odoo modules that contain email templates) isn't an attractive solution either,
as you would first have to sift through all the `mail_template_data.xml` files in all the Odoo modules, and there are more than 50.

## How to override email data templates

To override the email data templates, you need to be an administrator in Odoo and activate developer mode.
In the home menu (dashboard), type `Email Templates` for direct access, or go to `Settings` -> `Technical` -> `Email` -> `Email Templates`.

You should now see a list of all email data templates for each installed Odoo module.
Clicking on one of them will display the record properties, and show a WYSIWYG editor for the email body:

![Example of the WYSIWYG editor in Odoo](img/email_template_wysiwyg.png)

If you are in developer mode, you can select some text and click the `</>` button to see the HTML source code:

![Open HTML code view](img/email_code_view.png)

Now you can edit the HTML anyway you like. 

:warning: **Possible pitfalls**:

- Be careful with the placeholders in the HTML, as they are used by the Python code to insert the actual data.
  If you remove or rename a placeholder, the email might not be sent correctly.  
- Be careful with the CSS, as the email clients are very picky about what they support.
  You can use the [Campaign Monitor CSS guide](https://www.campaignmonitor.com/css/) to see what is supported where.
- When pasting HTML and saving it, Odoo performs some kind of sanitization, which might remove some of your code.  
  **Do NOT use self-closed tags**. Especially avoid `<t/>` tags, as the editor will rewrite them and add a `</t>` closing tag 
  somewhere at the end, which likely breaks your template at runtime. Write `<t></t>` tags instead, and if they are empty,
  the editor will properly rewrite them as `<t/>`. Also, do not use `<br/>` tags, but write `<br>` instead.

If you mess up, you can always revert to the original template by clicking the `Reset Template` button at the top.

**Note**: The HTML files in this folder are named according to the record `id`'s in the Odoo XML template files. 
These ID's are not visible in Odoo itself (record ID's are numeric in the database), but you can find the names of the 
template files in the `template_fs` field of the `mail_template` model in the database.

| Odoo name                    | File name                                 |
|------------------------------|-------------------------------------------|
| Payment: Payment Receipt     | mail_template_data_payment_receipt.html   |
| Invoice: Sending             | email_template_edi_invoice.html           |
| Credit Note: Sending         | email_template_edi_credit_note.html       |
| Calendar: Date Updated       | calendar_template_meeting_changedate.html |
| Calendar: Event Update       | calendar_template_meeting_update.html     |
| Calendar: Meeting Invitation | calendar_template_meeting_invitation.html |
| Calendar: Reminder           | calendar_template_meeting_reminder.html   |
| Helpdesk: Ticket Closed      | |
| Helpdesk: Ticket Received    | |
|                              | |

