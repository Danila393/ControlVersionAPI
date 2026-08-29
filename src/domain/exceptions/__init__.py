class BatchNotFoundError(Exception):
    pass


class BatchAlreadyExistsError(Exception):
    pass


class ProductNotFoundError(Exception):
    pass


class ProductAlreadyExistsError(Exception):
    pass


class ProductAlreadyAggregatedError(Exception):
    pass


class WebhookNotFoundError(Exception):
    pass
