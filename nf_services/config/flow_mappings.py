from nf_services.config.flow_mappings_config import generate_flow_definitions

def get_flow_map(flow_type, logic_flow, step_and_flow_construct_val, wallet=None, tackon="none"):
    flow_map = generate_flow_definitions(tackon)
    template = flow_map.get(step_and_flow_construct_val.lower(), {}).get(logic_flow.lower(), {})
    
    def replace_wallet(pair):
        return tuple(step.format(wallet=wallet) if wallet else step for step in pair)

    return [replace_wallet(pair) for pair in template.get(flow_type.lower(), [])] if template else []