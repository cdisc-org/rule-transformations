def _each_deep(
    context,
    before=lambda c, p, ip: None,
    after=lambda c, p, ip: None,
    path="",
    indexed_path="",
):
    node = context[-1]
    before(context, path, indexed_path)
    if hasattr(node, "items"):
        for key, value in node.items():
            _each_deep(
                context=context + [value],
                before=before,
                after=after,
                path=path + "/" + str(key),
                indexed_path=indexed_path + "/" + str(key),
            )
    elif type(node) == list:
        for key, value in enumerate(node):
            _each_deep(
                context=context + [value],
                before=before,
                after=after,
                path=path,
                indexed_path=indexed_path + "/" + str(key),
            )
    after(context, path, indexed_path)


def each_deep(node, before=lambda c, p, ip: None, after=lambda c, p, ip: None):
    _each_deep(context=[node], before=before, after=after)
    return node
