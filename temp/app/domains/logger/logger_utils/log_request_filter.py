def get_log_filter_options(request):

    return {
        "keyword":
            request.args.get(
                "keyword",
                default="",
                type=str
            ),

        "tag":
            request.args.get(
                "tag",
                default="전체",
                type=str
            ),

        "status":
            request.args.get(
                "status",
                default="전체",
                type=str
            ),

        "sort":
            request.args.get(
                "sort",
                default="최신순",
                type=str
            ),

        "per_page":
            request.args.get(
                "per_page",
                default=10,
                type=int
            ),

        "page":
            request.args.get(
                "page",
                default=1,
                type=int
            )
    }