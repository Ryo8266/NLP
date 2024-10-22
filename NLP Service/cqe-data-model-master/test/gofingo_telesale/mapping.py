# list of criteria needed in request body
criteria = [
    'greeting_agent', 'greeting_company', 'greeting',
    'identification_of_needs', 'identification_of_needs_close_question',
    # 'active_listening', 'impolite',
    'product_presentation_amount','product_presentation_period','product_presentation_payment_amount', 'product_advantage','sell_products', 'oh',
    'proactivity_amount', 'proactivity_period','proactivity',
    'ending_the_conversation'
]

# case 'audit_result' = yes
# map ground_truth column to criteria
map_criteria = {
    'Chào hỏi (2%)': ['greeting_agent', 'greeting_company'],
    'Xác định nhu cầu (8%)': ['identification_of_needs'],
    # 'Kiểm soát cảm xúc': ['impolite'],
    # 'Lắng nghe tích cực': ['active_listening'],
    'Giới thiệu sản phẩm (20%)': ['product_presentation_amount','product_presentation_period','product_presentation_payment_amount', 'product_advantage'],
    'Bán sản phẩm/dịch vụ (16%)': ['product_presentation', 'oh','sell_products'],
    'Giải quyết từ chối (14%)': ['oh'],
    'Tính chủ động (10%)': ['proactivity_amount', 'proactivity_period'],
    'Kết thúc cuộc trò chuyện (4%)': ['ending_the_conversation']
}

# case 'audit_result' = no
# map from ground_truth reason to smaller criteria
# IMPORTANT: given that every 'no' criteria will have 'reason', and every 'yes' criteria will have blank reason
map_reason_criteria = {
    'Không giới thiệu tên nhân viên':'greeting_agent',
    'Không giới thiệu tên công ty':'greeting_company',
    'Không giới thiệu tên nhân viên và công ty':'greeting',
    # 'Sử dụng câu hỏi đóng để xác định nhu cầu':'identification_of_needs_close_question',#identification_of_needs_close_question=yes
    'Không xác định nhu cầu':'identification_of_needs',
    'Không cung cấp thông tin khoản vay':['product_presentation_amount','product_presentation_period','product_presentation_payment_amount'],
    'Không cung cấp thông tin ưu điểm khoản vay':'product_advantage',
    'Không cung cấp thông tin khoản vay và ưu điểm khoản vay':['product_presentation_amount','product_presentation_period','product_presentation_payment_amount', 'product_advantage'],
    'Không xử lý từ chối':'oh',
    # 'Không xử lý từ chối đủ 3 lần':'oh',
    # 'Xử lý không đúng trọng tâm': 'oh',
    'Không chủ đông cung cấp thông tin số tiền tối đa':'proactivity_amount',
    'Không chủ động cung cấp thông tin thời hạn tối đa':'proactivity_period',
    'Không chủ đông cung cấp thông tin số tiền và thời hạn tối đa':'proactivity',
    'Không bán được sản phẩm/dịch vụ (trừ 50% điểm tiêu chí)':'sell_products',
    'Không chào và cám ơn khi kết thúc trò chuyện':'ending_the_conversation'
}