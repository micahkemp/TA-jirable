# encoding = utf-8

from jira import JIRA
from mako.template import Template

def process_event(helper, *args, **kwargs):
    """
    # IMPORTANT
    # Do not remove the anchor macro:start and macro:end lines.
    # These lines are used to generate sample code. If they are
    # removed, the sample code will not be updated when configurations
    # are updated.

    [sample_code_macro:start]

    # The following example gets the setup parameters and prints them to the log
    jira_url = helper.get_global_setting("jira_url")
    helper.log_info("jira_url={}".format(jira_url))
    username = helper.get_global_setting("username")
    helper.log_info("username={}".format(username))
    password = helper.get_global_setting("password")
    helper.log_info("password={}".format(password))

    # The following example gets the alert action parameters and prints them to the log
    project = helper.get_param("project")
    helper.log_info("project={}".format(project))

    unique_id_field_name = helper.get_param("unique_id_field_name")
    helper.log_info("unique_id_field_name={}".format(unique_id_field_name))

    unique_id_value = helper.get_param("unique_id_value")
    helper.log_info("unique_id_value={}".format(unique_id_value))

    issue_type = helper.get_param("issue_type")
    helper.log_info("issue_type={}".format(issue_type))

    summary = helper.get_param("summary")
    helper.log_info("summary={}".format(summary))


    # The following example adds two sample events ("hello", "world")
    # and writes them to Splunk
    # NOTE: Call helper.writeevents() only once after all events
    # have been added
    helper.addevent("hello", sourcetype="sample_sourcetype")
    helper.addevent("world", sourcetype="sample_sourcetype")
    helper.writeevents(index="summary", host="localhost", source="localhost")

    # The following example gets the events that trigger the alert
    events = helper.get_events()
    for event in events:
        helper.log_info("event={}".format(event))

    # helper.settings is a dict that includes environment configuration
    # Example usage: helper.settings["server_uri"]
    helper.log_info("server_uri={}".format(helper.settings["server_uri"]))
    [sample_code_macro:end]
    """

    helper.log_info("Alert action jirable started.")

    # jirable.py checks for the presence of these mandatory settings, so don't bother doing so here
    jira_url = helper.get_global_setting("jira_url")
    username = helper.get_global_setting("username")
    password = helper.get_global_setting("password")

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

    unique_id_field_name = helper.get_param("unique_id_field_name")
    helper.log_info("unique_id_field_name={}".format(unique_id_field_name))

    unique_id_value = helper.get_param("unique_id_value")
    helper.log_info("unique_id_value={}".format(unique_id_value))

    issue_type = helper.get_param("issue_type")
    helper.log_info("issue_type={}".format(issue_type))

    summary = helper.get_param("summary")
    helper.log_info("summary={}".format(summary))

    # JIRA forces setting customfields by customfield id instead of customfield name, so fetch the customfield info here to find our unique field id
    customfield_ids = {}
    for customfield in jira.fields():
        customfield_ids[customfield['name']] = customfield['id']
    unique_customfield_id = customfield_ids[unique_id_field_name]

    events = helper.get_events()
    for event in events:
        templated_unique_id_value = Template(unique_id_value).render(**event)
        helper.log_info("templated_unique_id_value: {}".format(templated_unique_id_value))

        matched = False
        # JIRA only allows CONTAINS searches against text fields, so we search for our full unique_id_value, then have to check for exact match against each found issue
        for existing_issue in jira.search_issues('project={} and {} ~ "{}" and status!=Done and status!=Resolved'.format(project, unique_id_field_name, templated_unique_id_value.replace('"', '\\"'))):
            try:
                # this is apparently how you do something like existing_issue.$unique_customfield_id
                existing_issue_unique_id_value = getattr(existing_issue.fields, unique_customfield_id)
                if existing_issue_unique_id_value == unique_id_value:
                    matched = True
            except:
                # it's fine if the custom field doesn't exist, because we're not sure if the events that matched have the field
                pass

        if not matched:
            issue = jira.create_issue(fields={'project': project, 'issuetype': {'name': issue_type}, 'summary': summary, unique_customfield_id: unique_id_value})

    return 0
