# Privatus Analytics for Dify

**You want to know how your website is doing, but you don't want to leave Dify to find out.**

Opening another dashboard, clicking through menus and copying numbers into a chat takes time. Many
analytics tools also use cookies. In many countries that means showing a cookie pop-up (the box
that asks visitors to accept cookies), and lots of people click "reject", so you never see them.

**Privatus Analytics counts the visitors to your website without cookies.** It never stores IP
addresses and keeps bots out of your numbers. This plugin brings those numbers into Dify.

**So you can just ask.** "How many people visited last week?" "Where did they come from?" "Is
anyone on the site right now?" Your Dify agent, chatflow or workflow gets the real numbers in
seconds, and you can send them on to a report, a message or any other step.

## What you can do

| Tool | What it gives you |
| --- | --- |
| **List Sites** | Your websites, with their site IDs and domains. |
| **Get Stats** | Visitors, visits, pageviews, bounce rate and visit time for a period, and how much they went up or down. |
| **Get Visitors Over Time** | The same numbers for each hour, day, week or month, ready for a chart or a trend. |
| **Get Top Pages, Referrers and More** | The top pages, entry and exit pages, referrers, channels, campaigns, countries, languages, devices, browsers, custom events or goals. |
| **Get Live Visitors** | How many people are on the site right now, and what they are looking at. |
| **List Goal Conversions** | Each goal with its conversions, conversion rate and change. |

Every tool only reads numbers. None of them changes or deletes anything in your account.

## Setup

1. **Get a Privatus Analytics account.** The Free plan has 10,000 events a month and 3 sites, with
   no card. Sign up at [privatusanalytics.com](https://privatusanalytics.com) and add the tracking
   script to your website.
2. **Create an API token.** In Privatus Analytics open **Workspace settings**, then **API tokens**,
   and create a token. It starts with `pat_`. The plugin only reads, so the token only needs permission to read analytics.
3. **Install the plugin.** In Dify open **Plugins**, search the Marketplace for
   **Privatus Analytics** and install it.
4. **Add your token.** Open the plugin, choose **Authorize** (or **API Key**), paste the token and
   save. Dify checks the token straight away.

## Usage

**In an agent or chatflow:** add the Privatus Analytics tools to the agent. Then ask in plain
words, for example:

- "How did privatusanalytics.com do in the last 7 days compared with the week before?"
- "What were the top 5 referrers this month?"
- "How many people are on my site right now?"
- "Which goal got the most conversions last month?"

The agent picks the tool and fills in the inputs.

**In a workflow:** add a tool node, pick a Privatus Analytics tool and fill in the inputs. Each tool
returns a short text summary and the full result as JSON for the next steps.

### Inputs

- **Site:** the site ID (like `pa_7Q2K9XH3AB`) or the domain (like `example.com`). Use **List Sites**
  to see them.
- **Period:** today, yesterday, the last 24 hours, the last 7, 14, 28, 30 or 90 days, this month,
  last month, this quarter, last quarter, this year, the last 12 months, last year, all time, or
  custom dates. Dates follow the timezone of the site.
- **Start date** and **End date:** only for custom dates, as `YYYY-MM-DD`.

## Connection

The plugin talks only to `https://privatusanalytics.com` over HTTPS, using the public
[Privatus Analytics API](https://privatusanalytics.com/docs/api). The API token is sent as a bearer
token in the `Authorization` header. Each request waits at most 30 seconds. Your Dify server needs
to be able to reach `privatusanalytics.com` on port 443.

## Privacy

The plugin stores nothing and logs nothing. It sends the token and the tool inputs to Privatus
Analytics, and nothing else. Read the full [privacy policy](PRIVACY.md).

## Source code and support

- Source repository: https://github.com/Privatus-Analytics/dify-plugin
- Contact: james@privatusanalytics.com
- API reference: https://privatusanalytics.com/docs/api

## License

MIT
