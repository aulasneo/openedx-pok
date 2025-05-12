from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def update_object(o, data):
    """
    Update a generic object with dict with data.

    """
    try:
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(getattr(o, key), datetime):
                    # Handle date time data
                    setattr(o, key, datetime.fromisoformat(value))
                elif isinstance(getattr(o, key), bool):
                    setattr(o, key, value.lower() == 'true')
                else:
                    setattr(o, key, value)
    except AttributeError as e:
        logger.error(f"Error '{e} updating {o} with {data}")


def split_name(full_name):
    """
    Splits a full name into first name and last name components.

    Args:
        full_name (str): The complete name to be split.

    Returns:
        tuple: A tuple containing (first_name, last_name)
            - If only one word is provided, it's considered the first name and last name is empty.
            - If two words are provided, the first is considered the first name and the second the last name.
            - If more than two words are provided, the first word is considered the first name and all remaining words are combined as the last name.

    Examples:
        >>> split_name("Leonardo")
        ('Leonardo', '')
        >>> split_name("Leonardo Beroes")
        ('Leonardo', 'Beroes')
        >>> split_name("Leonardo Antonio Beroes")
        ('Leonardo', 'Antonio Beroes')
    """
    if ',' in full_name:
        parts = full_name.split(',')
        return parts[1].strip(), parts[0].strip()

    parts = full_name.split()

    if not parts:
        return ""
    elif len(parts) == 1:
        return parts[0], ""
    elif len(parts) == 2:
        return parts[0], parts[1]
    elif len(parts) == 4:
        return ' '.join(parts[0:1]), ' '.join(parts[2:])
    else:
        # For compound names or multiple last names
        # This can be adjusted based on naming conventions in your region
        return parts[0], ' '.join(parts[1:])
