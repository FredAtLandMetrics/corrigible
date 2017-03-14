_rocket_mode = False

def rocket_mode(new_mode=None):
    """set mode if new_mode is defined. return current mode."""
    global _rocket_mode
    if new_mode is not None:
        _rocket_mode = new_mode
    return _rocket_mode
