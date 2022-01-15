# take first part of original migration script, retrieve eventive id and update eventive api request
# for security reasons, exclude all ticket bucket related data!!
from modules import eventive as e, notion as n

# SET EVENTS TO VISIBLE
# filter_dict = dict()
# n.add_filter_to_request_dict(filter_dict, property_name="eventive_id", property_type="text", filter_condition="is_not_empty", filter_content=True)
# notion_events = n.get_db('events', data_dict=filter_dict)
# item_count_notion = n.get_item_count(notion_events)
#
# for index in range(item_count_notion):
#     eventive_id = n.get_property(index, 'eventive_id', 'text', source=notion_events)
#     data_raw = {
#         "event_bucket": e.event_bucket_id,
#         "visibility": "visible",
#     }
#     e.update_event(data_raw, event_id=eventive_id)

# CHANGE STANDALONE TICKET BEHAVIOUR FOR INDUSTRY EVENTS

# filter_dict = dict()
# n.add_filter_to_request_dict(filter_dict, property_name="Type", property_type="select", filter_condition="equals", filter_content="Industry")
# notion_events = n.get_db('events', data_dict=filter_dict)
# item_count_notion = n.get_item_count(notion_events)
#
# for index in range(item_count_notion):
#     eventive_id = n.get_property(index, 'eventive_id', 'text', source=notion_events)
#     data_raw = {
#         "event_bucket": e.event_bucket_id,
#         "standalone_ticket_sales_enabled": False,
#         "standalone_ticket_sales_unlocked": False,
#     }
#     e.update_event(data_raw, event_id=eventive_id)
#
# # ENABLE TICKET BUTTON FOR ALL EVENTS
#
# filter_dict = dict()
# n.add_filter_to_request_dict(filter_dict, property_name="eventive_id", property_type="text", filter_condition="is_not_empty", filter_content=True)
# notion_events = n.get_db('events', data_dict=filter_dict)
# item_count_notion = n.get_item_count(notion_events)
#
# for index in range(item_count_notion):
#     eventive_id = n.get_property(index, 'eventive_id', 'text', source=notion_events)
#     data_raw = {
#         "event_bucket": e.event_bucket_id,
#         "hide_tickets_button": False,
#     }
#     e.update_event(data_raw, event_id=eventive_id)

# DISABLE TICKET SALES FOR ALL EVENTS

# filter_dict = dict()
# n.add_filter_to_request_dict(filter_dict, property_name="eventive_id", property_type="text", filter_condition="is_not_empty", filter_content=True)
# notion_events = n.get_db('events', data_dict=filter_dict)
# item_count_notion = n.get_item_count(notion_events)
#
# for index in range(item_count_notion):
#     eventive_id = n.get_property(index, 'eventive_id', 'text', source=notion_events)
#     data_raw = {
#         "event_bucket": e.event_bucket_id,
#         "sales_disabled_unless_coupon": True,
#     }
#     e.update_event(data_raw, event_id=eventive_id)

# ENABLE TICKET SALES FOR ALL EVENTS

filter_dict = dict()
n.add_filter_to_request_dict(filter_dict, property_name="eventive_id", property_type="text", filter_condition="is_not_empty", filter_content=True)
notion_events = n.get_db('events', data_dict=filter_dict)
item_count_notion = n.get_item_count(notion_events)

for index in range(item_count_notion):
    eventive_id = n.get_property(index, 'eventive_id', 'text', source=notion_events)
    data_raw = {
        "event_bucket": e.event_bucket_id,
        "sales_disabled_unless_coupon": False,
        "hide_tickets_button": False,
    }
    e.update_event(data_raw, event_id=eventive_id)