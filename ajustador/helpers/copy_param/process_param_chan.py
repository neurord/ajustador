
def create_chan_param_relation(new_param_chan, conds, start_block_lineno, end_block_lineno):
    valid_line_pattern = "(?P<chan>\w+)\s*=\s*(?P<func>\w+)\((?P<chanparams>[a-z0-9A-Z_,\s\[\]=]+).*"
    invalid_char_set = ('=', '[', ']')
    chan_param_relation = dict()
    with fileinput.input(files=(new_param_cond), inplace=True) as f_obj:
        for line in f_obj:
            if start_block_lineno < f_obj.lineno() < end_block_lineno:
                re_obj = re.search(valid_line_pattern, line)
                if re_obj:
                    chan_name, chan_params = re_obj.group('chan'), re_obj.group('chanparams')
                    chan_param_name_set = {sub_str for sub_str in chan_params.split(',') if not any(char in sub_str for char in invalid_char_set)}
                    chan_param_relation[chan_name] = chan_param_name_set
    return chan_param_relation
