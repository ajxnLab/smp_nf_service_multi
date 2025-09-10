from dotenv import load_dotenv
import os

def load_environment():
    """
    Load the base .env and the environment-specific overrides.
    """
    load_dotenv('.env')

    env_mode = os.getenv('APP_ENV')
 
    if env_mode == 'dev':
        load_dotenv('.env_dev', override=True)
    elif env_mode == 'prod':
        load_dotenv('.env_prod', override=True)
    else:
        print(f"[env_config] Warning: Unknown APP_ENV '{env_mode}', only .env loaded")

def get_env_variable(key: str) -> str:
    """
    Get an environment variable, raise error if not set.
    """
    value = os.getenv(key)

    if not value:
        raise ValueError(f"Environment variable '{key}' is not set!")
    
    return value
