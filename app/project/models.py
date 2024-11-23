class PaymentInformation:
    def __init__(self, card_number, cvv, expiration, name, billing_address, province, postal_code):
        self.card_number = card_number
        self.cvv = cvv
        self.expiration = expiration
        self.name = name
        self.billing_address = billing_address
        self.province = province
        self.postal_code = postal_code
