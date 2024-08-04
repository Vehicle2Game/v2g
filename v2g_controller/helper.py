debug_enabled = False

def range_map(x, in_min, in_max, out_min, out_max):
    if x < min(in_min, in_max):
        return out_min
    if x > max(in_min, in_max):
        return out_max
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def debug(msg, overwrite=False):
    if debug_enabled:
        if not overwrite:
            print(msg)
        else:
            print(msg, end="\r")