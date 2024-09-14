class ItemListError(Exception):
    pass


class StocksError(Exception):
    pass


class WrongShippingType(Exception):
    pass


class PaymentStatusError(Exception):
    pass


class CDEK_Error(Exception):
    pass


class PlacementError(Exception):
    pass


class RusPostIntegrationException(Exception):
    pass


class RetailCrmIntegrationError(Exception):
    pass
