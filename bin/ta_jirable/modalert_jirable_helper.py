# encoding = utf-8

from jira import JIRA

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

    # The following example gets the events that trigger the alert
    events = helper.get_events()
    for event in events:
        issue = jira.create_issue(fields={'project': project, 'issuetype': {'name': issue_type}, 'summary': summary})

    return 0
