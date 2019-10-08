def calc_g_tk(p_skey):
    t = 5381
    for c in p_skey:
        t += (t << 5) + ord(c)
    return t & 2147483647
