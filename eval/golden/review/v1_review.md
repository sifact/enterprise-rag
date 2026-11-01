# Golden set v1: draft review

Tick exactly one box per item. For `edit`, change the item in `v1_drafts.jsonl` and say what changed on the `Review note:` line.

## eng-fact-001

- Category: single_fact · asked as `engineering`
- Question: What is the name of the tool that appears when you type "pb" in GitLab to show a performance metrics bar?
- Answer: The tool is called Performance Bar.
- Evidence `handbook:engineering/data-engineering/database-excellence/database-operations/_index`: "Performance Bar: type `pb` in GitLab and a bar with performance metrics will show up at the top of the page. This tool is especially useful for viewing the queries executed and their timings."

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## eng-fact-002

- Category: single_fact · asked as `engineering`
- Question: Which frameworks does our architecture guidance point to for containing failures while a system grows?
- Answer: Swimlanes and the Scale Cube are the two models mentioned.
- Evidence `handbook:engineering/architecture/practice/scalability/index`: "[**Swimlanes**](https://akfpartners.com/growth-blog/fault-isolation-swim-lane) and the [**Scale Cube**](https://akfpartners.com/growth-blog/scale-cube) are widely adopted models to manage both fault isolation and scalability in a structured fashion."

- [ ] accept
- [x] edit
- [ ] drop

Review note: reworded question to avoid copying the source

## eng-fact-003

- Category: single_fact · asked as `engineering`
- Question: Which four elements are used to compute the capability fingerprint for job runner compatibility?
- Answer: The capability fingerprint is based on Tags, Runner Type, Protected Status, and Project Access.
- Evidence `handbook:engineering/architecture/design-documents/runner_job_router/_index`: "Tags: Exact tag matching requirements - Runner Type: Instance, group, or project-specific runners - Protected Status: Whether runner can handle protected references - Project Access: Which projects/groups the runner can access"

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## eng-fact-004

- Category: single_fact · asked as `engineering`
- Question: Which API does GitLab provide to retrieve EPSS scores for vulnerability reports?
- Answer: EPSS scores are reachable through the GitLab GraphQL API.
- Evidence `handbook:engineering/architecture/design-documents/epss/_index`: "EPSS scores may be populated from the EPSS Data page or through their provided API. Ultimately, EPSS scores should be reachable through the GitLab GraphQL API, as seen on the vulnerability report and details pages, and be filterable and usable when setting policies."

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## hr-fact-001

- Category: single_fact · asked as `hr`
- Question: If I stop contributing to the employee stock purchase plan, how do I get back in later?
- Answer: They must re‑enroll as a new participant during the next open enrollment window and begin a new Offering Period.
- Evidence `handbook:total-rewards/stock-options`: "Team members would need to re-enroll as a new participant in the next open enrollment window and begin a new Offering Period if they wish to participate in the future."

- [ ] accept
- [x] edit
- [ ] drop

Review note: question named the wrong plan (stock options vs ESPP)

## hr-fact-002

- Category: single_fact · asked as `hr`
- Question: Who runs the US Infectious Disease Policy and coordinates communication about it?
- Answer: People Operations oversees the policy's implementation and coordinates communications from management to team members and other stakeholders.
- Evidence `handbook:people-policies/inc-usa`: "People Operations will oversee the implementation of this policy and coordinate communications from management to team members and other stakeholders."

- [ ] accept
- [x] edit
- [ ] drop

Review note: question didn't say which policy

## hr-fact-003

- Category: single_fact · asked as `hr`
- Question: What three negative feedback styles can occur if a manager fails to both care personally and challenge directly?
- Answer: The possible negative styles are Ruinous Empathy, Manipulative Insincerity, and Obnoxious Aggression.
- Evidence `handbook:people-group/guidance-on-feedback`: "When you're not caring personally or challenging directly, it can lead to Ruinous Empathy, Manipulative Insincerity, or Obnoxious Aggression."

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## hr-fact-004

- Category: single_fact · asked as `hr`
- Question: According to the handbook, should 360 feedback be the sole factor when evaluating an employee's performance?
- Answer: No, the 360 feedback should not be the only data point used in evaluating performance; other observations must also be considered.
- Evidence `handbook:people-group/360-feedback`: "The feedback that your team member receives may reinforce excellent or under performance you have already observed, but shouldn't be the only data point you use in evaluating performance."

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## mkt-fact-001

- Category: single_fact · asked as `marketing`
- Question: According to the default ruleset, what status is assigned to a prospect who replies during a sequence?
- Answer: Qualifying.
- Evidence `handbook:marketing/marketing-operations/outreach/index`: "Once the first task of a sequence is completed, it will move the status to Accepted. - If a prospect replies, then it will move the status to Qualifying. - If a meeting is booked, then it will mark the sequence as finished and the status will be Qualifying."

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## mkt-fact-002

- Category: single_fact · asked as `marketing`
- Question: Is the Google Sheets registration export switched on automatically for every Accelevents event?
- Answer: No. It's only activated automatically for events created from the GitLab Epic Conference Template, but it can be activated and configured for any other event.
- Evidence `handbook:marketing/marketing-operations/accelevents`: "Note: Registration exports to Sheets is only activated automatically on events created from the `GitLab Epic Conference Template` template, but can be activated and configured for any event."

- [ ] accept
- [x] edit
- [ ] drop

Review note: answer went beyond the quoted evidence; narrowed question and answer

## mkt-fact-004

- Category: single_fact · asked as `marketing`
- Question: How many business days before month‑end does Digital Marketing need to verify accruals?
- Answer: Digital Marketing must verify accruals 4-5 business days before the end of the month.
- Evidence `handbook:marketing/growth-marketing/digital-agency/agency`: "Digital Marketing must verify accruals 4-5 business days before the end of the month, making sure all Allocadia IDs/Coupa POs are correct and estimated spends are within range."

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## mkt-fact-005

- Category: single_fact · asked as `marketing`
- Question: How long should I wait for Allocadia to finish syncing with Salesforce before modifying the SFDC campaign?
- Answer: It can take up to 5 minutes for Allocadia to sync with Salesforce.
- Number: 5 minutes (scale 1)
- Evidence `handbook:marketing/growth-marketing/partner-and-industry-marketing/mdf-operations-process`: "It can take up to 5 minutes for Allocadia to sync with Salesforce. Don’t edit the SFDC campaign until the sync."

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## legal-fact-001

- Category: single_fact · asked as `legal`
- Question: Once a partner's Letter of Authorization request comes in, what happens to it before it's fully executed?
- Answer: The LOA goes to the Legal team for a Legal Stamp, then to a GitLab authorized signatory to execute, and the fully executed LOA is distributed via DocuSign to GitLab Legal and the partner.
- Evidence `handbook:legal/customer-negotiations`: "the LOA will be routed to the Legal team to add a Legal Stamp, and then to a GitLab authorized signatory for execution. Upon completion, the fully executed LOA will be distributed via DocuSign to GitLab Legal and the partner"

- [ ] accept
- [x] edit
- [ ] drop

Review note: answer trimmed to what the quote supports

## legal-fact-002

- Category: single_fact · asked as `legal`
- Question: Where are the Official Rules for each promotional game permanently hosted?
- Answer: The Official Rules are permanently hosted at /handbook/legal/promotional-game-standard-rules/.
- Evidence `handbook:legal/process-for-ux-research-prize-draws/index`: "There is a set of Official Rules which applies for every Promotional Game offered and is permanently hosted [here](/handbook/legal/promotional-game-standard-rules/)."

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## legal-fact-003

- Category: single_fact · asked as `legal`
- Question: What right does a customer forfeit concerning AI‑generated output that is identical or similar to that produced for GitLab or other third‑party users?
- Answer: The customer has no claim of right, title, or interest against GitLab or third‑party end users to the extent such claim relates to the same, or similar output generated for GitLab or other third‑party end users.
- Evidence `handbook:legal/ai-functionality-terms`: "Customer has no claim of right, title, or interest against GitLab or third‑party end users to the extent such claim relates to the same, or similar output generated for GitLab or other third‑party end users."

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## legal-fact-004

- Category: single_fact · asked as `legal`
- Question: What is the maximum number of referral fees GitLab will pay for a single transaction?
- Answer: GitLab will never pay more than one (1) Referral Fee for a single transaction related to Products and Services.
- Evidence `handbook:legal/reseller-agreement`: "GitLab will never pay more than one (1) Referral Fee for a single transaction related to Products and Services."

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## sales-fact-001

- Category: single_fact · asked as `sales`
- Question: Can I use Field Operations office hours for a recurring project status check-in?
- Answer: No. Office hours aren't meant for checking on a project's status or as a recurring project meeting.
- Evidence `handbook:sales/field-operations/_index`: "Office hours are NOT a dedicated time for team members to join to check in on the status of a project or to be used as a recurring project meeting."

- [ ] accept
- [x] edit
- [ ] drop

Review note: question didn't say whose office hours

## sales-fact-002

- Category: single_fact · asked as `sales`
- Question: On which day of the week do individual contributors receive the Update Ticker by email?
- Answer: Individual contributors receive the Update Ticker by email on Thursdays.
- Evidence `handbook:sales/field-communications/field-update-tickers`: "Members of the Target Audience (listed above) can expect to receive the Update Ticker via email on Thursdays."

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## sales-fact-003

- Category: single_fact · asked as `sales`
- Question: When I have a reseller‑direct deal, who should receive the quote?
- Answer: Send the quote to your reseller contact only and do not copy the customer.
- Evidence `handbook:sales/field-operations/channel-operations/sales-faq`: "The quote needs to be sent to the partner, not the customer. Specifically, if your quote is: - reseller-direct, send the quote to your reseller contact only (ensure you do not copy the customer)"

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## sales-fact-004

- Category: single_fact · asked as `sales`
- Question: Which field competency is about using repeatable processes and managing my time and daily workload well?
- Answer: Process Discipline.
- Evidence `handbook:sales/training/field-functional-competencies`: "Process Discipline Leverages repeatable and scalable processes and tools throughout the customer lifecycle. Effectively manages time, priorities, and daily workload to effectively engage customers."

- [ ] accept
- [x] edit
- [ ] drop

Review note: question copied the definition

## fin-fact-001

- Category: single_fact · asked as `finance`
- Question: What aspect of GitLab did Jessica Ross highlight as the most compelling factor in her decision to join the company?
- Answer: She emphasized the culture, noting GitLab’s commitment to learning, iteration, and building in the open as the key attraction.
- Evidence `handbook:finance/readmes/jessica-ross`: "What stood out most was not just the product, but the culture. GitLab’s commitment to learning, iteration, and building in the open deeply aligns with how I lead and how I grow."

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## fin-fact-002

- Category: single_fact · asked as `finance`
- Question: What details must be entered on the Planned Personnel sheet for an internal movement placeholder before the candidate is identified?
- Answer: You must add a row with the headcount Name set to "TBH", the Hire Status set to "Placeholder", and leave the salary fields blank.
- Evidence `handbook:finance/financial-planning-and-analysis/adaptive-insights`: "On the Planned Personnel sheet, create an entry/row for the internal movement placeholder. Enter the headcount Name as "TBH", the Hire Status as "Placeholder" and ensure no salary information is included."

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## fin-fact-003

- Category: single_fact · asked as `finance`
- Question: What are the main purposes of GitLab's Global Travel & Expense Policy?
- Answer: The policy is intended to provide guidance on allowable reimbursable expenses, ensure efficient use of team members' time, increase transparency of business travel spend, highlight the safety, visibility, support and savings from a centralized travel program, and prevent violations of anti‑bribery and corruption laws.
- Evidence `handbook:finance/expenses`: "Provide guidance around allowable reimbursable expenses. Ensure the best utilization of our Team Member's time. Drive transparency across all business travel related spend. Help Team Members understand that a centralized travel program results in improved safety, visibility, support and savings. Prevent violations of applicable anti-bribery and corruption laws."

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## fin-fact-004

- Category: single_fact · asked as `finance`
- Question: Who holds the global Director position for Billing & Collections?
- Answer: Tim Cheeney is the Director of Billing & Collections globally.
- Evidence `handbook:finance/accounting/finance-ops/billing-ops/_index`: "- [Tim Cheeney](https://gitlab.com/tcheeney) - Director, Billing & Collections (Global) - [Josephine Hararah](https://gitlab.com/josephinehararah) - Senior Manager, Billing Operations (Global) - [Kinga Polgardi](https://gitlab.com/kingapolgardi) - Manager, Billing Operations (EMEA and APAC)"

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## gen-001

- Category: general_page · asked as `engineering`
- Question: At what exact UTC time does a sandbox resource expire according to the shutdown label?
- Answer: The expiration occurs at 23:59:59 UTC on the calculated shutdown date.
- Evidence `handbook:company/infrastructure-standards/realms/sandbox/labels-tags`: "The expiration time is calculated as 23:59:59 UTC on the date calculated from the `gl_sandbox_shutdown_after_days` value and the timestamp the resources was initially provisioned in the cloud provider."

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## gen-002

- Category: general_page · asked as `finance`
- Question: Who is listed as the Executive Sponsor for the merge‑request‑report‑widgets working group and what is their title?
- Answer: Tim Zallmann is the Executive Sponsor, holding the title Director of Engineering, Dev.
- Evidence `handbook:company/working-groups/merge-request-report-widgets`: "Working Group Role | Person | Stakeholder Dept. | Title | ------------------ | ------------------------ | ------------------------- | --------------------------------------------- | | Executive Sponsor | Tim Zallmann | Dev | Director of Engineering, Dev"

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## gen-004

- Category: general_page · asked as `legal`
- Question: What must be completed before the self‑service working group can implement any system changes?
- Answer: The Zuora SSOT must be completed as a prerequisite before any system changes are made by the working group.
- Evidence `handbook:company/working-groups/ecommerce`: "*note: [Zuora SSOT](https://gitlab.com/groups/gitlab-org/-/epics/4664) is a prerequisite of any system changes coming out of this working group.*"

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## gen-005

- Category: general_page · asked as `engineering`
- Question: Which tool is recommended for remote workers to visually signal their availability with a color system?
- Answer: The Luxafor Flag light indicator is recommended for signaling availability.
- Evidence `handbook:company/culture/all-remote/workspace`: "For example, the [Luxafor Flag](https://luxafor.com/product/flag/) light indicator utilizes a color system to alert those around you (or outside of your home office) whether or not they are free to interrupt without requesting permission."

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## gen-006

- Category: general_page · asked as `sales`
- Question: What dataset size qualifies as large enough to warrant using the time‑decay effect for performance optimization?
- Answer: A dataset is considered large if it exceeds roughly 50 million records or 100 GB in size.
- Evidence `handbook:company/working-groups/database-scalability/time-decay`: "In contrast, large datasets over ~50 Million records and/or 100GB in size add a significant overhead to constantly accessing a really small subset of the data."

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## gen-007

- Category: general_page · asked as `hr`
- Question: Who is the executive sponsor of the Maintainership working group, and what is their title?
- Answer: Christopher Lefelhocz, VP of Development.
- Evidence `handbook:company/working-groups/maintainership`: "Executive Sponsor | Christopher Lefelhocz | VP of Development | Facilitator | Michelle Gill | Senior Engineering Manager, Manage Functional Lead (Enablement) | Alex Ives"

- [ ] accept
- [x] edit
- [ ] drop

Review note: question didn't say which working group

## mh-004

- Category: multi_hop · asked as `legal`
- Question: What does the handbook require when adding a third‑party trademark to GitLab, and what liability does GitLab disavow for such activities?
- Answer: The handbook requires that you follow the defined steps for adding new third‑party trademarks or using an approved trademark for a new purpose, and GitLab disclaims liability for any special, incidental or consequential damages, procurement costs, interruption of use, loss or corruption of data, or any other damages.
- Evidence `handbook:legal/policies/product-third-party-trademarks-guidelines`: "Follow these steps when adding new third-party trademarks to GitLab, or intending to use an already approved third-party trademark in GitLab for a new purpose."
- Evidence `handbook:legal/policies/website-terms-of-use`: "In no event will GitLab or any of its affiliates, suppliers or licensors, be liable with respect to any subject matter of this Agreement under any contract, negligence, strict liability or other legal or equitable theory for:"

- [ ] accept
- [ ] edit
- [x] drop

Review note: two unrelated questions joined; second quote doesn't hold the answer

## mh-005

- Category: multi_hop · asked as `sales`
- Question: What is the scheduled date for the GitLab Partner webcast targeting the APAC region, and what major update to the quote‑to‑cash process is being rolled out on August 3 2021?
- Answer: The APAC Partner webcast is scheduled for May 5, and on August 3 2021 we are implementing multiple Partner Program and System changes to greatly simplify the quote‑to‑cash process.
- Evidence `handbook:sales/field-communications/field-flash-newsletter/edition-2021-05-03`: "Channel Webinars - [GitLab Partner Webcast (APAC)](https://www.brighttalk.com/webcast/18613/483881?utm_source=GitLabInc&utm_medium=brighttalk&utm_campaign=483881) - May 5 - [GitLab Partner Webcast (AMER & EMEA)](https://www.brighttalk.com/webcast/18613/483879?utm_source=GitLabInc&utm_medium=brighttalk&utm_campaign=483879) - May 6"
- Evidence `handbook:sales/field-communications/field-flash-newsletter/edition-2021-08-02`: "On 2021-08-03, we are **implementing multiple Partner Program and System changes** to greatly simplify the quote to cash process and add significant sales value."

- [ ] accept
- [ ] edit
- [x] drop

Review note: two unrelated newsletter facts joined

## mh-006

- Category: multi_hop · asked as `finance`
- Question: How is Exit ARR calculated in the revenue model, and what defines Total Net New Starts in the headcount metrics?
- Answer: Exit ARR is calculated as Beginning ARR plus New Booked Net ARR plus Growth Booked Net ARR plus Booking Timing Adjustments minus Trueups plus Deviation Amount. Total Net New Starts are defined as Total Starts excluding Internal Hires.
- Evidence `handbook:finance/financial-planning-and-analysis/adaptive-insights`: "Beginning ARR + New Booked Net ARR + Growth Booked Net ARR + Booking Timing Adjustments + (-1*Trueups) + Deviation Amount = Exit ARR"
- Evidence `handbook:finance/financial-planning-and-analysis/headcount-metrics-and-processes`: "- **Total Net New Starts**: <ins>Total Starts</ins> excluding <ins>Internal Hires</ins>. - **Total Gross Starts**: <ins>Total Starts</ins> including <ins>Internal Hires</ins>."

- [ ] accept
- [ ] edit
- [x] drop

Review note: two unrelated definitions joined

## mh-008

- Category: multi_hop · asked as `hr`
- Question: What approval steps must be completed before a job description can be merged, and what is the process for submitting a referral when the role is only open internally?
- Answer: First, the direct manager reviews and validates the description, then Talent Management checks level consistency, followed by the Department Head and People Business Partner confirming the business need, and finally Total Rewards ensures market‑level data, that all sections are populated, and creates the Workday title. For an internal‑only vacancy, the recruiter assigns the issue, confirms it is marked confidential, then adds the referral in Greenhouse via the “+ > Add a Referral” screen, fills the required fields from the issue, updates the source credit, sends the default confirmation email from the no‑reply alias, and closes the issue.
- Evidence `handbook:hiring/job-description-library`: "Your manager: Your direct manager is responsible for clarifying the scope of responsibilities and level of roles, ensuring clear differentiation between levels, and checking responsibilities and requirements and ensuring the job description follows the template logic and **has all of the required areas**. Mangers should validate business need for the role with their direct manager."
- Evidence `handbook:hiring/referral-operations`: "If the vacancy is **only** open internally, go to your Greenhouse dashboard and click `+` > `Add a Referral`. Reference the Issue to see what should be entered in the following fields:"

- [ ] accept
- [ ] edit
- [x] drop

Review note: two unrelated processes joined; answer goes far beyond the quotes

## mh-009

- Category: multi_hop · asked as `marketing`
- Question: When setting up a Partner Marketing MDF activity, which line item is used to create the Marketo program and what naming pattern must be applied to the cloned program?
- Answer: The Marketo program should be created using the Channel MDF line item, and the cloned program must be named using the pattern YYYYMMDD__MDF_000_PartnerName_EventName_Region.
- Evidence `handbook:marketing/growth-marketing/partner-and-industry-marketing/mdf-operations-process`: "Right click "YYYYMMDD__MDF_000_PartnerName_EventName_Region" and hit "Clone" 1. Clone to - select Campaign folder 1. Name - paste the Campaign Name from Allocadia 1. Folder - insert the `FY#- Q# - MDF Campaigns`"
- Evidence `handbook:marketing/growth-marketing/partner-and-industry-marketing/hyperscalers`: "Program and Payment Coordination: 1. Use Channel MDF line item to create Marketo program (aligns with standard channel processes) 2. Use Hyperscaler MDF line items for Zip payment request"

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## fin-sec-002

- Category: sec_lookup · asked as `finance`
- Question: What was GitLab's total revenue for the fiscal year ended January 31, 2026?
- Answer: GitLab reported total revenue of $955,224 thousand for the fiscal year ended January 31, 2026.
- Number: 955224 USD (scale 1000)
- Evidence `sec:10-K:2026-01-31` p142: "Revenue: Subscription—self-managed and SaaS $ 864,704 $ 675,179 $ 506,306 License—self-managed and other 90,520 84,070 73,600 Total revenue 955,224 759,249 579,906"

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## fin-sec-004

- Category: sec_lookup · asked as `finance`
- Question: What was the amount of net deferred tax assets reported for the fiscal year ending January 31, 2026?
- Answer: The net deferred tax assets were $25,556 thousand.
- Number: 25556 USD (scale 1000)
- Evidence `sec:10-K:2026-01-31` p190: "Gross deferred tax assets 355,702 347,032 Valuation allowance (330,146) (323,710) Net deferred tax assets 25,556 23,322 Deferred tax liabilities:"

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## fin-sec-005

- Category: sec_lookup · asked as `finance`
- Question: What was the total amount of accrued expenses and other current liabilities reported for the fiscal year ending January 31, 2026?
- Answer: Total accrued expenses and other current liabilities were $58,185 thousand (about $58.2 million) as of January 31, 2026.
- Number: 58185 USD (scale 1000)
- Evidence `sec:10-K:2026-01-31` p171: "Other current liabilities 187 275 Total accrued expenses and other current liabilities $ 58,185 $ 54,680"

- [ ] accept
- [x] edit
- [ ] drop

Review note: answer rewritten as a sentence with the date

## fin-sec-006

- Category: sec_lookup · asked as `finance`
- Question: What were GitLab’s total current assets reported for the year ended January 31 2026?
- Answer: GitLab’s total current assets were $1,655,779 thousand as of January 31 2026.
- Number: 1.65578e+06 USD (scale 1000)
- Evidence `sec:10-K:2026-01-31` p141: "Prepaid expenses and other current assets 48,899 40,411 Total current assets 1,655,779 1,336,317 Property and equipment, net 11,815 4,013"

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## fin-sec-007

- Category: sec_lookup · asked as `finance`
- Question: What was the total revenue for the six months ended July 31, 2026, and how much higher was it than the same period in 2025?
- Answer: $550.4 million in total revenue for the six months ended July 31, 2026, which is $99.9 million (22%) higher than the $450.5 million reported for the same period in 2025.
- Number: 550.4 USD (scale 1000000)
- Evidence `sec:10-Q:2026-07-31` p60: "Revenue increased $99.9 million, or 22%, to $550.4 million for the six months ended July 31, 2026 from $450.5 million for the six months ended July 31, 2025."

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## fin-sec-008

- Category: sec_lookup · asked as `finance`
- Question: What was the amount of total cash equivalents and short‑term investments reported on January 31, 2026?
- Answer: The total cash equivalents and short‑term investments were $850,480 thousand as of January 31, 2026.
- Number: 850480 USD (scale 1000)
- Evidence `sec:10-Q:2026-07-31` p28: "Total cash equivalents and short-term investments $ 850,480 $ (2,431) $ — $ — $ 850,480 $ (2,431)"

- [ ] accept
- [ ] edit
- [x] drop

Review note: misreads a table of investments in an unrealized-loss position

## fin-sec-010

- Category: sec_lookup · asked as `finance`
- Question: What was the total fair value of cash equivalents and short‑term investments as of January 31, 2026?
- Answer: The total fair value of cash equivalents and short‑term investments was $1,183,068 (in thousands).
- Number: 1.18307e+06 USD (scale 1000)
- Evidence `sec:10-Q:2026-07-31` p26: "Total short-term investments 1,028,878 1,533 (84) 1,030,327 Total cash equivalents and short-term investments $ 1,181,619 $ 1,533 $ (84) $ 1,183,068"

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## fin-sec-011

- Category: sec_lookup · asked as `finance`
- Question: What was JiHu's net income for the three months ended July 31, 2026?
- Answer: JiHu reported net income of $1,542 thousand for the three months ended July 31, 2026.
- Number: 1542 USD (scale 1000)
- Evidence `sec:10-Q:2026-07-31` p39: "Income (loss) from operations 1,473 (2,029) 58 (3,047) Interest income 110 155 217 320 Other income (expense), net (35) (45,491) (48) (45,466) Net income (loss) $ 1,542 $ (47,367) $ 220 $ (48,196)"

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## mh-002

- Category: multi_hop · asked as `hr`
- Question: What is the longest stretch of consecutive calendar days a team member can take as PTO without needing special approval, and what is the recommended approach for returning to work after such time off?
- Answer: A team member can take up to 25 consecutive calendar days of PTO without special permission. Upon returning, they should expect a transition period and avoid feeling pressured to work extra hours.
- Number: 25 days (scale 1)
- Evidence `handbook:people-group/time-off-and-absence/time-off-types`: "time off exceeding 25 consecutive calendar days (including weekends and holidays), special permission is required from your Manager, People Business Partner, and the Absence Management Team at leaves@gitlab.com."
- Evidence `handbook:people-group/time-off-and-absence/time-away-philosophy`: "Expect a transition period – It's normal to need time to catch up after returning. Don't feel pressured to work extra hours before or after your time away."

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## mh-003

- Category: multi_hop · asked as `marketing`
- Question: Which dashboard should I use to modify the landing page scripts, and what is the first action an SDR should take when relevance fields are populated?
- Answer: You should edit landing page scripts in the White Label Plan dashboard under Integrations → Landing page, and the SDR’s first step is to review the Relevance_Priority__c field.
- Evidence `handbook:marketing/marketing-operations/accelevents`: "Custom scripts created by the Accelevents team exist in the `Landing Page` settings, found under `Integrations -> Landing page`. Do not adjsut these settings as doing so will affect registration forms."
- Evidence `handbook:marketing/marketing-operations/usergems`: "When the fields are available: 1. Review `Relevance_Priority__c` to understand the recommended priority. 2. Read `Relevance_Summary__c` to understand the key signals."

- [ ] accept
- [ ] edit
- [x] drop

Review note: two unrelated facts joined

## mh-005-s43

- Category: multi_hop · asked as `sales`
- Question: What are the attendance requirements for the Command of the Message portion of the Value Sales Methodology, and where can a new sales hire learn what “meeting expectations” means for their role?
- Answer: New sales hires must attend the full Command of the Message (CoM) value‑sales methodology class, which is delivered as four two‑hour live virtual sessions (or, if live attendance isn’t possible, complete the recordings and required practice sessions), and attendance is recorded as part of Academy measurement. They can learn what “meeting expectations” means for their specific sales role by reviewing the Field Sales Roles & Expectations learning objective in the onboarding material.
- Evidence `handbook:sales/onboarding/sqs-learning-objectives`: "Discover the different sales roles at GitLab and identify what constitutes "meeting expectations" when it comes to your particular role."
- Evidence `handbook:sales/onboarding/graduating-sqs`: "Attend the full **Command of the Message (CoM) / value sales methodology class**, typically delivered as four 2-hour live virtual sessions covering GitLab's sales methodology, sales process, and value messaging."

- [ ] accept
- [ ] edit
- [x] drop

Review note: two unrelated facts joined; answer goes beyond the quotes

## mh-006-s43

- Category: multi_hop · asked as `finance`
- Question: When an expense is flagged as out of policy and needs clarification, who contacts the employee, and what quarterly task does the finance committee perform regarding disclosure controls?
- Answer: The AP team contacts the team member via Navan, and each quarter the Committee reviews and evaluates the effectiveness of the company’s disclosure control procedures.
- Evidence `handbook:finance/expenses`: "Upon review, if more clarification is needed for a certain expense, the AP team will contact the team member via Navan to ask for justification of the transaction before approving or rejecting the expense."
- Evidence `handbook:finance/committee-composition`: "Each quarter, the Committee shall review and evaluate the effectiveness of the company's procedures for recording, processing, summarizing and reporting information required to be disclosed by the company in its Exchange Act filings."

- [ ] accept
- [ ] edit
- [x] drop

Review note: two unrelated facts joined

## mh-007

- Category: multi_hop · asked as `engineering`
- Question: What prompted the move from service‑based runbooks to alert‑based playbooks, and how did the incident pattern in mid‑2019 influence this decision?
- Answer: The transition was driven by the shortcomings of existing runbooks, which were mainly architectural and lacked direct troubleshooting steps, and by a spike in customer‑facing incidents during July‑September 2019 that highlighted the need for faster, alert‑focused response guidance.
- Evidence `handbook:engineering/infrastructure-platforms/alert-playbook-management`: "Our current runbooks tend to be more architectural documents or contain many links to unrelated information without much troubleshooting guidance. Moreover, they are primarily service-based runbooks."
- Evidence `handbook:engineering/infrastructure-platforms/team-history`: "Throughout July, August, and September 2019, GitLab.com experienced a higher than normal amount of customer-facing incidents, including mirroring delays, slowdowns, and vertical node scaling issues. This placed higher expectations on the Infrastructure department and highlighted the need for a dedicated team focused on scalability."

- [ ] accept
- [ ] edit
- [x] drop

Review note: answer invents a causal link the passages don't state

## fin-sec-017

- Category: sec_lookup · asked as `finance`
- Question: What is the projected range of total charges for the 2027 restructuring plan?
- Answer: The company expects total charges under the 2027 Plan to be approximately $30 million to $35 million.
- Number: 30 USD (scale 1000000)
- Evidence `sec:10-Q:2026-07-31` p36: "The Company expects total charges under the 2027 Plan to be approximately $30 million to $35 million, inclusive of amounts recognized to date."

- [x] accept
- [ ] edit
- [ ] drop

Review note:

## mh-101

- Category: multi_hop · asked as `finance`
- Question: I need to buy a $7,000 software tool. Can I put it on my corporate card or just expense it, and if not, how do I buy it?
- Answer: Neither. Corporate card purchases shouldn't exceed $5,000 per transaction, and Navan only takes single expense items up to $5,000; anything above $5,000 goes through the procurement process in Zip.
- Evidence `handbook:finance/accounts-payable/corp-credit-cards`: "Purchases on your card should not exceed $5,000 USD for each transaction annually."
- Evidence `handbook:finance/expenses`: "Expense claims for a single item up to $5,000 can be expensed via Navan. >$5,000 needs to go through the procurement process in Zip."

- [x] accept
- [ ] edit
- [ ] drop

Review note: written by hand during review: LLM multi-hop drafts joined unrelated facts

## mh-102

- Category: multi_hop · asked as `legal`
- Question: We want to run a conference sweepstakes with three $250 prizes, open to attendees in New Zealand. Is that allowed?
- Answer: Not as planned. The $750 total is under the general $1,000 aggregate cap, but New Zealand can only be included if all prizes together are worth less than $500.
- Evidence `handbook:legal/process-for-a-conference-sweepstakes`: "The total aggregate value of all prizes must be less than $1,000 USD. See #5.10. and #5.11. for exceptions."
- Evidence `handbook:legal/process-for-a-conference-sweepstakes`: "New Zealand can be included provided the total aggregate value of all prizes is less than $500 USD."

- [x] accept
- [ ] edit
- [ ] drop

Review note: written by hand during review: LLM multi-hop drafts joined unrelated facts

## mh-103

- Category: multi_hop · asked as `sales`
- Question: A partner's deal registration lapsed and we need roughly six more weeks on it. Who can push the date out that far?
- Answer: The Channel Account Manager can only extend an expired DR by 30 days. For anything longer, chatter @Partner Operations with the new date the registration should expire.
- Evidence `handbook:sales/field-operations/channel-operations/sales-faq`: "Yes, the expired DR can be extended for 30 days by the Channel Account Manager. Please chatter the Channel Account Manager to request that they extend the DR. If you need an extension longer than 30 days, please chatter `@Partner Operations` and provide the new date the registration should expire."

- [x] accept
- [ ] edit
- [ ] drop

Review note: written by hand during review: LLM multi-hop drafts joined unrelated facts

## mh-104

- Category: multi_hop · asked as `engineering`
- Question: If our Sec on-call rotation shrank to 3 engineers rotating weekly, would that still be within our on-call limits? What should I do?
- Answer: No. With 3 people rotating weekly each engineer is on call about 1 week in every 3, but nobody should be on call more than once every 4 weeks, so tell your manager immediately.
- Evidence `handbook:engineering/development/sec/oncall/joining-and-leaving-rotation`: "You should never be on-call more than once every 4 weeks. If you find yourself exceeding this, tell your manager immediately—it's a signal that we need to adjust staffing or reduce alert volume."
- Evidence `handbook:engineering/development/sec/oncall/joining-and-leaving-rotation`: "If you have 7 engineers in APAC and you rotate weekly: - Each engineer is on-call roughly 1 week every 7 weeks"

- [x] accept
- [ ] edit
- [ ] drop

Review note: written by hand during review: LLM multi-hop drafts joined unrelated facts

# User spot-check

17 items sampled at random (seed from configs/eval.yaml) from every source. Note any change under the item; edits are recorded in `notes`.

### eng-fact-001 (single_fact, asked as `engineering`, answer)

- Question: What is the name of the tool that appears when you type "pb" in GitLab to show a performance metrics bar?
- Answer: The tool is called Performance Bar.
- Evidence `handbook:engineering/data-engineering/database-excellence/database-operations/_index`: "Performance Bar: type `pb` in GitLab and a bar with performance metrics will show up at the top of the page. This tool is especially useful for viewing the queries executed and their timings."
- Notes: drafted by openai/gpt-oss-120b (draft-v1)

User comment:

### sales-fact-002 (single_fact, asked as `sales`, answer)

- Question: On which day of the week do individual contributors receive the Update Ticker by email?
- Answer: Individual contributors receive the Update Ticker by email on Thursdays.
- Evidence `handbook:sales/field-communications/field-update-tickers`: "Members of the Target Audience (listed above) can expect to receive the Update Ticker via email on Thursdays."
- Notes: drafted by openai/gpt-oss-120b (draft-v1)

User comment:

### fin-fact-002 (single_fact, asked as `finance`, answer)

- Question: What details must be entered on the Planned Personnel sheet for an internal movement placeholder before the candidate is identified?
- Answer: You must add a row with the headcount Name set to "TBH", the Hire Status set to "Placeholder", and leave the salary fields blank.
- Evidence `handbook:finance/financial-planning-and-analysis/adaptive-insights`: "On the Planned Personnel sheet, create an entry/row for the internal movement placeholder. Enter the headcount Name as "TBH", the Hire Status as "Placeholder" and ensure no salary information is included."
- Notes: drafted by openai/gpt-oss-120b (draft-v1)

User comment:

### fin-fact-003 (single_fact, asked as `finance`, answer)

- Question: What are the main purposes of GitLab's Global Travel & Expense Policy?
- Answer: The policy is intended to provide guidance on allowable reimbursable expenses, ensure efficient use of team members' time, increase transparency of business travel spend, highlight the safety, visibility, support and savings from a centralized travel program, and prevent violations of anti‑bribery and corruption laws.
- Evidence `handbook:finance/expenses`: "Provide guidance around allowable reimbursable expenses. Ensure the best utilization of our Team Member's time. Drive transparency across all business travel related spend. Help Team Members understand that a centralized travel program results in improved safety, visibility, support and savings. Prevent violations of applicable anti-bribery and corruption laws."
- Notes: drafted by openai/gpt-oss-120b (draft-v1)

User comment:

### gen-002 (general_page, asked as `finance`, answer)

- Question: Who is listed as the Executive Sponsor for the merge‑request‑report‑widgets working group and what is their title?
- Answer: Tim Zallmann is the Executive Sponsor, holding the title Director of Engineering, Dev.
- Evidence `handbook:company/working-groups/merge-request-report-widgets`: "Working Group Role | Person | Stakeholder Dept. | Title | ------------------ | ------------------------ | ------------------------- | --------------------------------------------- | | Executive Sponsor | Tim Zallmann | Dev | Director of Engineering, Dev"
- Notes: drafted by openai/gpt-oss-120b (draft-v1)

User comment:

### gen-007 (general_page, asked as `hr`, answer)

- Question: Who is the executive sponsor of the Maintainership working group, and what is their title?
- Answer: Christopher Lefelhocz, VP of Development.
- Evidence `handbook:company/working-groups/maintainership`: "Executive Sponsor | Christopher Lefelhocz | VP of Development | Facilitator | Michelle Gill | Senior Engineering Manager, Manage Functional Lead (Enablement) | Alex Ives"
- Notes: drafted by openai/gpt-oss-120b (draft-v1); edited in review: question didn't say which working group

User comment:

### fin-sec-004 (sec_lookup, asked as `finance`, answer)

- Question: What was the amount of net deferred tax assets reported for the fiscal year ending January 31, 2026?
- Answer: The net deferred tax assets were $25,556 thousand.
- Evidence `sec:10-K:2026-01-31` p190: "Gross deferred tax assets 355,702 347,032 Valuation allowance (330,146) (323,710) Net deferred tax assets 25,556 23,322 Deferred tax liabilities:"
- Notes: drafted by openai/gpt-oss-120b (draft-v1)

User comment:

### mh-101 (multi_hop, asked as `finance`, answer)

- Question: I need to buy a $7,000 software tool. Can I put it on my corporate card or just expense it, and if not, how do I buy it?
- Answer: Neither. Corporate card purchases shouldn't exceed $5,000 per transaction, and Navan only takes single expense items up to $5,000; anything above $5,000 goes through the procurement process in Zip.
- Evidence `handbook:finance/accounts-payable/corp-credit-cards`: "Purchases on your card should not exceed $5,000 USD for each transaction annually."
- Evidence `handbook:finance/expenses`: "Expense claims for a single item up to $5,000 can be expensed via Navan. >$5,000 needs to go through the procurement process in Zip."
- Notes: written by hand during review: LLM multi-hop drafts joined unrelated facts

User comment:

### fin-xlsx-004 (spreadsheet_lookup, asked as `finance`, answer)

- Question: How many people is Sales planning to hire in Q3?
- Answer: Sales plans 20 hires in Q3, against 11 expected departures.
- Evidence `synthetic:headcount_fy2027` p3: "Sales,Q3,20,11,12 Sales,Q4,25,13,15"
- Notes: computed from the synthetic workbooks with pandas (computed.py)

User comment:

### fin-xlsx-005 (spreadsheet_lookup, asked as `finance`, answer)

- Question: Which cloud hosting provider has the largest annual plan, and how much is it?
- Answer: Northwind Cloud is the largest cloud hosting vendor, with an FY2027 plan of $2,661,000.
- Evidence `synthetic:vendor_spend_fy2027` p2: "Northwind Cloud,Cloud hosting,Engineering,2661000,665200,692500 Bluepeak Compute,Cloud hosting,Engineering,1613000,408500,362800"
- Notes: computed from the synthetic workbooks with pandas (computed.py)

User comment:

### fin-xlsx-006 (spreadsheet_lookup, asked as `finance`, answer)

- Question: How much did we actually pay Supportly in the first quarter?
- Answer: Actual Q1 spend with Supportly was $158,700.
- Evidence `synthetic:vendor_spend_fy2027` p2: "Supportly,SaaS tools,Customer Success,597000,158700,128300 Codeguard,Security tools,Engineering,577000,139800,137200"
- Notes: computed from the synthetic workbooks with pandas (computed.py)

User comment:

### oos-003 (out_of_scope, asked as `finance`, refuse)

- Question: What is GitLab's stock price right now?
- Notes: hand-written; real-time data the corpus doesn't hold

User comment:

### fin-cross-004 (cross_source_finance, asked as `finance`, answer)

- Question: How many customers paying $100,000 or more in ARR did we add between the end of fiscal 2026 and July 31, 2026?
- Answer: 115. There were 1,456 such customers as of January 31, 2026 and 1,571 as of July 31, 2026.
- Evidence `sec:10-K:2026-01-31` p24: "Our success has been exemplified by the growth in our $100,000 ARR customers to 1,456 as of January 31, 2026, from 1,229 as of January 31, 2025."
- Evidence `sec:10-Q:2026-07-31` p49: "our $100,000 ARR customers increased to 1,571 as of July 31, 2026 from 1,344 as of July 31, 2025, an increase of 17%."
- Notes: hand-written; numbers checked against the filing text

User comment:

### clevel-004 (c_level, asked as `c_level`, answer)

- Question: Who runs the US Infectious Disease Policy and coordinates communication about it?
- Answer: People Operations oversees the policy's implementation and coordinates communications from management to team members and other stakeholders.
- Evidence `handbook:people-policies/inc-usa`: "People Operations will oversee the implementation of this policy and coordinate communications from management to team members and other stakeholders."
- Notes: twin: hr-fact-002; derived c_level item

User comment:

### xrole-003 (cross_role, asked as `hr`, refuse)

- Question: How many people is Sales planning to hire in Q3?
- Must not see: synthetic:headcount_fy2027
- Notes: twin: fin-xlsx-004; derived cross-role item

User comment:

### xrole-010 (cross_role, asked as `legal`, refuse)

- Question: Which API does GitLab provide to retrieve EPSS scores for vulnerability reports?
- Must not see: handbook:engineering/architecture/design-documents/epss/_index
- Notes: twin: eng-fact-004; derived cross-role item

User comment:

### xrole-012 (cross_role, asked as `sales`, refuse)

- Question: When setting up a Partner Marketing MDF activity, which line item is used to create the Marketo program and what naming pattern must be applied to the cloned program?
- Must not see: handbook:marketing/growth-marketing/partner-and-industry-marketing/hyperscalers, handbook:marketing/growth-marketing/partner-and-industry-marketing/mdf-operations-process
- Notes: twin: mh-009; derived cross-role item

User comment:
