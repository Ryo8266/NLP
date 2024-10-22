# list of criteria needed in request body
criteria = [
    'greet','agentIntroduce','companyName',
    'confirmCustomer',
    'informAmount','informOverdue',
    'requestPayment',
    'askPaymentDatetime', 'askPaymentAmount', 'askPaymentMethod', 'askPaymentReceipt',
    'willpaySummary', 'nopaySummary', 'paidSummary', 'callResult', 'objectHandling',
    'goodbye','thank',
    'callResult'
]

map_criteria_simple = {
    'Identification of client': ['confirmCustomer'],
    'Will you pay': ['requestPayment'],
    'When': ['askPaymentDatetime'],
    'How much': ['askPaymentAmount'],
    'Where': ['askPaymentMethod'],
    'Payment receipt': ['askPaymentReceipt'],
    'Call Result': ['callResult']
}

map_criteria_complex = {
    'Greeting': ['greet','agentIntroduce','companyName'],
    'Reason of the call': ['informAmount','informOverdue'],
    'Summary structure': ['goodbye','thank'],
    'Contain all information': ['willpaySummary', 'nopaySummary', 'paidSummary'],
    'OH1 handle': ['objectHandling'],
    'OH2 handle': ['objectHandling'],
}