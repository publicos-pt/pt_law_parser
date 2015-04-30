from pt_law_parser import expressions


def from_json(data):

    def _decode(data_dict):
        values = []
        if isinstance(data_dict, str):
            return data_dict

        assert(len(data_dict) == 1)
        klass_string = next(iter(data_dict.keys()))
        klass = getattr(expressions, klass_string)

        args = []
        for e in data_dict[klass_string]:
            x = _decode(e)
            if isinstance(x, str):
                args.append(x)
            else:
                args += x
        values.append(klass(*args))

        return values

    return _decode(data)[0]
