import hashlib


def uuid_to_color(uuid_str):
    hash_val = hashlib.md5(uuid_str.encode()).hexdigest()

    # Use part of hash to determine hue
    hue = int(hash_val[:6], 16) % 360

    # Fix saturation & lightness for good visibility
    return f"hsl({hue}, 65%, 55%)"