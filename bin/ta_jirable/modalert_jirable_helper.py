# encoding = utf-8

from jira import JIRA
from mako.template import Template
import re
import splunklib.client as client
import json
from datetime import datetime

def process_event(helper, *args, **kwargs):
    helper.log_info("Alert action jirable started.")

    # addinfo adds _search_et, _search_lt, _timestamp to helper.info
    # we use these fields for the kvstore, so grab them up here (just once)
    helper.addinfo()

    # jirable.py checks for the presence of these mandatory settings, so don't bother doing so here
    jira_url = helper.get_global_setting("jira_url")
    username = helper.get_global_setting("username")
    password = helper.get_global_setting("password")
    dynamic_field_prefix = helper.get_global_setting("dynamic_field_prefix")

    # unique_id_field_name is optional, and is not checked in jirable.py
    unique_id_field_name = helper.get_global_setting("unique_id_field_name")

    # try to connect, bail out if unable to do so
    jira = None
    try:
        jira = JIRA(jira_url, basic_auth=(username, password))
    except:
        helper.log_info("Unable to connect to JIRA.  Check URL and authentication settings.")
        return 1

    # The following example gets the alert action parameters and prints them to the log
    project = helper.get_param("project")
    helper.log_info("project={}".format(project))

    unique_id_value = helper.get_param("unique_id_value")
    helper.log_info("unique_id_value={}".format(unique_id_value))

    issue_type = helper.get_param("issue_type")
    helper.log_info("issue_type={}".format(issue_type))

    summary = helper.get_param("summary")
    helper.log_info("summary={}".format(summary))

    dedup_by_unique_id_value = helper.get_param("dedup_by_unique_id_value")
    helper.log_info("dedup_by_unique_id_value={}".format(dedup_by_unique_id_value))

    # quit if asked to dedup without the unique field name
    # note that "yes" is hardcoded, and this is the string that must be in savedsearches.conf
    # the use of 0, false, etc is not supported
    if dedup_by_unique_id_value=="yes" and not unique_id_field_name:
        helper.log_info("Dedup by Unique ID Value was checked, but Unique ID Field Name is not set.  Bailing out.")
        return 1

    # JIRA forces setting customfields by customfield id instead of customfield name, so fetch the customfield info here to find our unique field id
    customfield_ids = {}
    for customfield in jira.fields():
        customfield_ids[customfield['name']] = customfield['id']
    # we fetched all field ids, but only set unique_customfield_id if we have unique_id_field_name

    events = helper.get_events()
    for event in events:
        templated_project           = Template(project).render(**event)
        templated_issue_type        = Template(issue_type).render(**event)
        templated_summary           = Template(summary).render(**event)

        # what our new issue will look like (to start with)
        issue_fields = {
            'project': templated_project,
            'issuetype': {'name': templated_issue_type},
            'summary': templated_summary,
        }

        # a new issue will be created if issue remains False
        issue = False

        # don't bother searching unless configured to dedup
        if dedup_by_unique_id_value=="yes":

            templated_unique_id_value  = Template(unique_id_value).render(**event)
            unique_customfield_id = customfield_ids[unique_id_field_name]
            issue_fields[unique_customfield_id] = templated_unique_id_value

            # JIRA only allows CONTAINS searches against text fields, so we search for our full unique_id_value, then have to check for exact match against each found issue
            for existing_issue in jira.search_issues('{} ~ "{}" and status!=Done and status!=Resolved'.format(unique_id_field_name, templated_unique_id_value.replace('"', '\\"'))):
                try:
                    # this is apparently how you do something like existing_issue.$unique_customfield_id
                    existing_issue_unique_id_value = getattr(existing_issue.fields, unique_customfield_id)
                    if existing_issue_unique_id_value == templated_unique_id_value:
                        issue = existing_issue
                        jira_action = "append"
                except:
                    # it's fine if the custom field doesn't exist, because we're not sure if the events that matched have the field
                    pass

        # issue = False if not asked to dedup or if no matching dedup issue was found
        if not issue:
            issue = jira.create_issue(fields=issue_fields)
            jira_action = "create"

            dynamic_field_regex = re.compile(r"^" + dynamic_field_prefix + "(?P<dynamic_field_name>.*)$")
            for field in event:
                match = dynamic_field_regex.match(field)
                if match:
                    try:
                        issue.update(fields={customfield_ids[match.group('dynamic_field_name')]: event[field]})
                    except:
                        # in case a dynamic field was improperly named, etc, don't bail out, just log it
                        helper.log_info("Unable to set field: {}".format(match.group('dynamic_field_name')))

        # new or existing issue, we continue processing to add to the kvstore
        session_key = helper.session_key

        # need to set owner="nobody" to use kvstore
        service = client.connect(owner="nobody", token=session_key)
        jirables_collection = service.kvstore['jirables']
        jirables_collection.data.insert(
            json.dumps({
                "jira_key": issue.key,
                # _timestamp is the time the search was run
                "alert_time": helper.info.get('_timestamp'),
                # if no _search_et, use start of time (0)
                "search_et": helper.info.get('_search_et', 0),
                # if no _search_lt, use the time of the search
                "search_lt": helper.info.get('_search_lt', helper.info.get('_timestamp')),
                "jira_action": jira_action,
            })
        )

    return 0
