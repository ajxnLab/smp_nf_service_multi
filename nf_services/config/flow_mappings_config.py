from nf_services.nf_constants import TackOn

def generate_flow_definitions(tackon="none"):
    # Define check flows conditionally
    base_check = [("CHECK_HAS_SUBSCRIPTION", "IN_CHARGE")] if tackon == TackOn.CHECK_HAS_ADD.value else []
    double_check = [("CHECK_HAS_SUBSCRIPTION", "IN_CHARGE")] if tackon == TackOn.CHECK_HAS_ADD.value else []
    opm_check = [("CHECK_HAS_SUBSCRIPTION", "EXTEND_FIRST_EXPIRY")] if tackon == TackOn.CHECK_HAS_ADD.value else []

    # Define base flow configurations
    BASE_FLOWS = {
        "check": base_check,
        "charge": [("IN_CHARGE", "EXTEND_FIRST_EXPIRY")],
        "extend": [("IN_CHARGE", "EXTEND_FIRST_EXPIRY"), ("EXTEND_FIRST_EXPIRY", "{wallet}")],
        "data": [("EXTEND_FIRST_EXPIRY", "{wallet}"), ("{wallet}", "SMS_ALLNET_UNLI")],
        "sms": [("{wallet}", "SMS_ALLNET_UNLI"), ("SMS_ALLNET_UNLI", "VOICE_ALLNET_UNLI")],
        "voice": [("SMS_ALLNET_UNLI", "VOICE_ALLNET_UNLI"), ("VOICE_ALLNET_UNLI", "HLR_PLY")],
    }

    DOUBLE_FLOWS = {
        "check": double_check,
        "data": [("EXTEND_FIRST_EXPIRY", "DOUBLE_{wallet}"), ("DOUBLE_{wallet}", "DOUBLE_SMS_ALLNET_UNLI")],
        "sms": [("{wallet}", "DOUBLE_SMS_ALLNET_UNLI"), ("DOUBLE_SMS_ALLNET_UNLI", "DOUBLE_VOICE_ALLNET_UNLI")],
        "voice": [("DOUBLE_SMS_ALLNET_UNLI", "DOUBLE_VOICE_ALLNET_UNLI")],
    }

    EXTEND_FLOWS = {
        "charge": [("EXTEND_CHARGE", "EXTEND_FIRST_EXPIRY")],
        "data": [("EXTEND_FIRST_EXPIRY", "EXTEND_{wallet}"), ("EXTEND_{wallet}", "EXTEND_SMS_ALLNET_UNLI")],
        "sms": [("{wallet}", "EXTEND_SMS_ALLNET_UNLI"), ("EXTEND_SMS_ALLNET_UNLI", "EXTEND_VOICE_ALLNET_UNLI")],
        "voice": [("EXTEND_SMS_ALLNET_UNLI", "EXTEND_VOICE_ALLNET_UNLI")],
    }

    BASE_FLOWS_OPM = {
        "check": opm_check,
        "extend": [("EXTEND_FIRST_EXPIRY", "{wallet}")],
        "data": [("EXTEND_FIRST_EXPIRY", "{wallet}"), ("{wallet}", "SMS_ALLNET_UNLI")],
        "sms": [("{wallet}", "SMS_ALLNET_UNLI"), ("SMS_ALLNET_UNLI", "VOICE_ALLNET_UNLI")],
        "voice": [("SMS_ALLNET_UNLI", "VOICE_ALLNET_UNLI"), ("VOICE_ALLNET_UNLI", "HLR_PLY")],
    }

    BASE_FLOWS_SMS_VOICE_BULK = {
        "check": base_check,
        "charge": [("IN_CHARGE", "EXTEND_FIRST_EXPIRY")],
        "extend": [("IN_CHARGE", "EXTEND_FIRST_EXPIRY"), ("EXTEND_FIRST_EXPIRY", "{wallet}")],
        "data": [("EXTEND_FIRST_EXPIRY", "{wallet}"), ("{wallet}", "SMS_ALLNET_UNLI")],
        "sms": [("{wallet}", "SMS_ALLNET_UNLI"), ("SMS_ALLNET_UNLI", "VOICE_ALLNET_UNLI")],
        "voice": [("SMS_ALLNET_UNLI", "VOICE_ALLNET_UNLI"), ("VOICE_ALLNET_UNLI", "HLR_PLY")],
    }

    ROAM_PREPAID_TRIGGER = {
        "roaming prepaid trigger service": [
            ("hlr_set_vssr", "hlr_set_diamrrs"),
            ("hlr_set_diamrrs", "data_prov"),
        ],
        "roaming prepaid main service": [
            ("hlr_set_vssr", "hlr_set_diamrrs"),
            ("hlr_set_diamrrs", "extend_first_expiry"),
            ("extend_first_expiry", "data_prov"),
        ]
    }

    ROAM_POSTPAID_TRIGGER = {
        "roaming postpaid trigger service": [
            ("sdm_postpaid", "data_prov"),
        ],
        "roaming postpaid main service": [
            ("sdm_postpaid", "in_charge"),
            ("in_charge", "data_prov"),
        ]
    }

    # Define the complete flow map
    FLOW_MAP = {
        "prepaid ctl with data, bulk sms and bulk voice": {
            "base": BASE_FLOWS,
            "double": DOUBLE_FLOWS,
        },
        "prepaid ctl with data, unli sms and unli voice": {
            "base": BASE_FLOWS,
            "double": DOUBLE_FLOWS,
            "extend": EXTEND_FLOWS,
        },
        "prepaid ctl with data and unli sms": {
            "base": {
                "check": base_check,
                "charge": BASE_FLOWS["charge"],
                "extend": BASE_FLOWS["extend"],
                "data": BASE_FLOWS["data"],
                "sms": [("{wallet}", "SMS_ALLNET_UNLI")],
            },
            "double": {
                "check": double_check,
                "data": DOUBLE_FLOWS["data"],
                "sms": [("{wallet}", "DOUBLE_SMS_ALLNET_UNLI")],
            },
            "extend": {
                "charge": EXTEND_FLOWS["charge"],
                "data": EXTEND_FLOWS["data"],
                "sms": [("{wallet}", "EXTEND_SMS_ALLNET_UNLI")],
            },
            },
            "prepaid ctl with unli sms and unli voice": {
            "base": {
                "check": base_check,
                "charge": BASE_FLOWS["charge"],
                "extend": [("IN_CHARGE", "EXTEND_FIRST_EXPIRY"), ("EXTEND_FIRST_EXPIRY", "SMS_ALLNET_UNLI")],
                "sms": [("EXTEND_FIRST_EXPIRY", "SMS_ALLNET_UNLI"), ("SMS_ALLNET_UNLI", "VOICE_ALLNET_UNLI")],
                "voice": [("SMS_ALLNET_UNLI", "VOICE_ALLNET_UNLI"), ("VOICE_ALLNET_UNLI", "HLR_PLY")],
            },
            "double": {
                "check": double_check,
                "sms": [("EXTEND_FIRST_EXPIRY", "DOUBLE_SMS_ALLNET_UNLI"), ("DOUBLE_SMS_ALLNET_UNLI", "DOUBLE_SMS_ALLNET_UNLI")],
                "voice": [("DOUBLE_SMS_ALLNET_UNLI", "DOUBLE_VOICE_ALLNET_UNLI")],
            },
            "extend": {
                "charge": EXTEND_FLOWS["charge"],
                "sms": [("EXTEND_FIRST_EXPIRY", "EXTEND_SMS_ALLNET_UNLI"), ("EXTEND_SMS_ALLNET_UNLI", "EXTEND_SMS_ALLNET_UNLI")],
                "voice": EXTEND_FLOWS["voice"],
            },
        },
        "prepaid ctl with data": {
            "base": {
                "check": base_check,
                "charge": BASE_FLOWS["charge"],
                "extend": BASE_FLOWS["extend"],
                "data": [("EXTEND_FIRST_EXPIRY", "{wallet}")],
            },
            "double": {
                "check": double_check,
                "data": [("EXTEND_FIRST_EXPIRY", "DOUBLE_{wallet}")],
            },
            "extend": {
                "charge": EXTEND_FLOWS["charge"],
                "data": [("EXTEND_FIRST_EXPIRY", "EXTEND_{wallet}")],
            },
        },
        "prepaid opm with data, unli sms and unli voice": {
            "check": opm_check,
            "base": BASE_FLOWS_OPM,
            "double": DOUBLE_FLOWS,
            "extend": EXTEND_FLOWS,
        },
        "prepaid opm with data and unli sms": {
            "base": {
                "check": opm_check,
                "extend": BASE_FLOWS_OPM["extend"],
                "data": BASE_FLOWS_OPM["data"],
                "sms": [("{wallet}", "SMS_ALLNET_UNLI")],
            },
            "double": {
                "check": opm_check,
                "data": DOUBLE_FLOWS["data"],
                "sms": [("{wallet}", "DOUBLE_SMS_ALLNET_UNLI")],
            },
            "extend": {
                "charge": EXTEND_FLOWS["charge"],
                "data": EXTEND_FLOWS["data"],
                "sms": [("{wallet}", "EXTEND_SMS_ALLNET_UNLI")],
            },
        },
        "prepaid opm with data and unli voice": {
            "base": {
                "check": opm_check,
                "extend": BASE_FLOWS_OPM["extend"],
                "data": [("EXTEND_FIRST_EXPIRY", "{wallet}"), ("{wallet}", "VOICE_ALLNET_UNLI")],
                "voice": [("{wallet}", "VOICE_ALLNET_UNLI"), ("VOICE_ALLNET_UNLI", "HLR_PLY")],
            },
            "double": {
                "check": opm_check,
                "data": [("EXTEND_FIRST_EXPIRY", "DOUBLE_{wallet}"), ("DOUBLE_{wallet}", "DOUBLE_VOICE_ALLNET_UNLI")],
                "voice": [("DOUBLE_{wallet}", "DOUBLE_VOICE_ALLNET_UNLI")],
            },
            "extend": {
                "charge": EXTEND_FLOWS["charge"],
                "data": [("EXTEND_FIRST_EXPIRY", "EXTEND_{wallet}"), ("EXTEND_{wallet}", "EXTEND_VOICE_ALLNET_UNLI")],
                "voice": [("EXTEND_{wallet}", "EXTEND_VOICE_ALLNET_UNLI")],
            },
        },
        "prepaid opm with unli sms and unli voice": {
            "base": {
                "check": opm_check,
                "extend": [("EXTEND_FIRST_EXPIRY", "SMS_ALLNET_UNLI")],
                "sms": [("EXTEND_FIRST_EXPIRY", "SMS_ALLNET_UNLI"), ("SMS_ALLNET_UNLI", "VOICE_ALLNET_UNLI")],
                "voice": [("SMS_ALLNET_UNLI", "VOICE_ALLNET_UNLI"), ("VOICE_ALLNET_UNLI", "HLR_PLY")],
            },
            "double": {
                "check": opm_check,
                "sms": [("EXTEND_FIRST_EXPIRY", "DOUBLE_SMS_ALLNET_UNLI"), ("DOUBLE_SMS_ALLNET_UNLI", "DOUBLE_VOICE_ALLNET_UNLI")],
                "voice": [("DOUBLE_SMS_ALLNET_UNLI", "DOUBLE_VOICE_ALLNET_UNLI")],
            },
            "extend": {
                "charge": EXTEND_FLOWS["charge"],
                "sms": [("EXTEND_FIRST_EXPIRY", "EXTEND_SMS_ALLNET_UNLI"), ("EXTEND_SMS_ALLNET_UNLI", "EXTEND_VOICE_ALLNET_UNLI")],
                "voice": EXTEND_FLOWS["voice"],
            },
        },
        "prepaid opm with data": {
            "base": {
                "check": opm_check,
                "extend": BASE_FLOWS_OPM["extend"],
                "data": [("EXTEND_FIRST_EXPIRY", "{wallet}")],
            },
            "double": {
                "check": opm_check,
                "data": [("EXTEND_FIRST_EXPIRY", "DOUBLE_{wallet}")],
            },
            "extend": {
                "charge": EXTEND_FLOWS["charge"],
                "data": [("EXTEND_FIRST_EXPIRY", "EXTEND_{wallet}")],
            },
        },
    }

    return FLOW_MAP

# Initialize with default setting
FLOW_MAP = generate_flow_definitions(tackon="none")