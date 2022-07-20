import yaml

from google.cloud import dialogflowcx_v3 as cx
from google.protobuf.struct_pb2 import Value

from vocaptcha.server import VoCaptchaServer, VoCaptchaManager

manager = VoCaptchaManager()
config = manager.config

app = VoCaptchaServer(
    plugins=config.plugins,
    collection=config.collection,
    plugin_folder=config.pluginFolder,
    agent_name=config.agentName,
    flow_name=config.flowName
)

app.inject_webhooks()
app.inject_pages()
app.patch_router_page()
app.patch_start_flow()

# app.inject_pages()
# app.patch_start_flow()
# app.patch_router_page()

# app.patch_flow()

# start_flow = app.flows_client.get_flow(
#     name=app.flow_name
# )
# transition_route = start_flow.transition_routes[0]
# print(transition_route)

# router = app.current_pages.get('Router')
# print(router.transition_routes)
# plugin_count = len(app.plugins)
# router_ranges = [
#     (
#         round(n /plugin_count, ndigits=2),
#         round((n+1) /plugin_count, ndigits=2)
#     ) for n in range(plugin_count)
# ]

# conditions = [
#     (
#         f"$session.params.which-challenge > {lower} "
#         f"AND $session.params.which-challenge <= {upper}"
#     ) for lower, upper in router_ranges
# ]

# generate_pages = [
#     page
#     for display_name, page in app.current_pages.items()
#     if display_name.startswith("generate")
# ]

# transition_routes = [
#     {
#         "condition": condition,
#         "target_page": page.name,
#         "trigger_fulfillment": {}  
#     } for condition, page in zip(conditions, generate_pages)
# ]
# router.transition_routes = transition_routes
# result = app.pages_client.update_page(
#     page = router
# )
# print(result)

# trigger_fulfillment = transition_route.trigger_fulfillment
# set_action_parameter = cx.Fulfillment.SetParameterAction(
#     parameter = "apples",
#     value = Value(string_value="yummy apples")
# )
# json_set_action_parameter = dict(
#     parameter = "apples-v2",
#     value = dict(string_value="my new string with apples")
# )
# print(trigger_fulfillment.set_parameter_actions)
# print(len(trigger_fulfillment.set_parameter_actions))
# trigger_fulfillment.set_parameter_actions.append(set_action_parameter)
# trigger_fulfillment.set_parameter_actions.append(json_set_action_parameter)
# result = app.flows_client.update_flow(
#     flow = start_flow
# )
# print(result)
