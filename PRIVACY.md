# Privacy Policy: Privatus Analytics plugin for Dify

This plugin connects Dify to Privatus Analytics (https://privatusanalytics.com).

## What the plugin sends

When a tool runs, the plugin sends a request to `https://privatusanalytics.com`
and to no other host. The request holds:

- your Privatus Analytics API token, in the `Authorization` header;
- the inputs of the tool: the site ID or domain, the period or dates, the
  report and the number of rows.

It does not send your prompts, chat messages, files or any other content of
your Dify app.

## What the plugin stores and logs

The plugin itself does not collect, store or log any user data. It keeps no
files, uses no database and writes nothing to logs. Dify keeps the API token
you enter, encrypted, as it does for every tool credential.

## What Privatus Analytics does with the request

Privatus Analytics reads the numbers you ask for and sends them back. Requests
made with an API token are handled under the Privatus Analytics privacy policy:
https://privatusanalytics.com/legal/privacy

The numbers themselves come from cookieless tracking. Privatus Analytics does
not use cookies and does not keep IP addresses or personal profiles of the
visitors to your website.

## Third parties

The plugin shares no data with any third party other than Privatus Analytics.

## Contact

Questions about this policy: james@privatusanalytics.com
