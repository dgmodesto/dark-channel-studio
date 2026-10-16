class ApiError(Exception):
    """Error rendered as `{code, params}`; never carries localized text."""

    def __init__(self, status_code: int, code: str, **params: object):
        self.status_code, self.code, self.params = status_code, code, params
        super().__init__(code)
