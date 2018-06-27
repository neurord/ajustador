# TODO write descriptor and explain functionality.

def get_units_scale_factor(prefix):
	units_prefix = {"y":1e-24, "z":1e-21, "a":1e-18, "f":1e-15, "p": 1e-12,
	                "n":1e-9, "u":1e-6, "µ":1e-6, "m":1e-3, "c":1e-2, "d":0.1,
                        "h":100, "k":1000, "M":1e6, "G":1e9, "T":1e12, "P":1e15,
                        "E":1e18, "Z":1e21, "Y":1e14}
	try:
	    return units_prefix[prefix]
	except KeyError as e:
            print("Invalid scaling factor {}!!! please check your inputs csv.".format(prefix))
            return 1.0
