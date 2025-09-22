# Custom Exceptions


class BulkServiceError(Exception):
    pass


class ExpiryServiceError(BulkServiceError):
    pass


class WalletError(BulkServiceError):
    pass


class GSheetUpdateError(BulkServiceError):
    pass
#